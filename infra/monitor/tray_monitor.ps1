# Ícone na bandeja do Windows com o uso do servidor ao vivo.
#
# Mantém UMA conexão ssh aberta rodando `live_top.py --json`, que manda uma linha
# JSON por amostra. A cada linha o ícone é redesenhado (barra de RAM e barra de
# VRAM, cor = dono) e o tooltip recebe os números.
#   clique esquerdo  -> abre o monitor completo no Windows Terminal
#   clique direito   -> menu (abrir, reconectar, sair)
#
# Rode escondido:  powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File tray_monitor.ps1
# O instalar_monitor.ps1 cria o atalho na pasta Inicializar para subir junto com o Windows.
param(
    [string]$Server   = $(if ($env:B3_HOST) { $env:B3_HOST } else { "fernando.murusaki@10.10.10.151" }),
    [string]$Key      = "$env:USERPROFILE\.ssh\id_benchmark",
    [string]$Script   = "$PSScriptRoot\live_top.py",
    [string]$Launcher = "$PSScriptRoot\monitor_servidor.bat",
    [int]$Interval    = 5
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public class TrayIconApi {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern bool DestroyIcon(IntPtr handle);
}
"@

# uma instância só: o segundo processo sai calado
$mutex = New-Object System.Threading.Mutex($true, "Global\MonitorServidorTray", [ref]$null)
if (-not $mutex.WaitOne(0)) { exit }

# mesmas cores do terminal (xterm 34/82, 170, 33, 166, 246, 238)
$COL = @{
    me     = [Drawing.Color]::FromArgb(0, 175, 0);    me_model = [Drawing.Color]::FromArgb(95, 255, 0)
    other  = [Drawing.Color]::FromArgb(215, 95, 215); docker   = [Drawing.Color]::FromArgb(255, 135, 0)
    system = [Drawing.Color]::FromArgb(148, 148, 148); cache   = [Drawing.Color]::FromArgb(68, 68, 68)
    free   = [Drawing.Color]::FromArgb(38, 38, 38);   dead     = [Drawing.Color]::FromArgb(120, 40, 40)
}

function Get-PartColor([string]$key, [string]$me) {
    # chave do JSON: "dono|tipo"
    $owner, $kind = $key -split '\|', 2
    if ($kind -eq 'cache')            { return $COL.cache }
    if ($owner -eq 'sistema')         { return $COL.system }
    if ($owner -like 'docker*')       { return $COL.docker }
    if ($owner -eq $me)               { return $(if ($kind -eq 'model') { $COL.me_model } else { $COL.me }) }
    if ($owner -like "*$me*")         { return $COL.me_model }   # "você + fulano" no mesmo modelo
    return $COL.other
}

function New-TrayIcon($data) {
    # 32x32: barra da RAM à esquerda, da VRAM à direita, preenchendo de baixo para cima
    $bmp = New-Object Drawing.Bitmap 32, 32
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.Clear([Drawing.Color]::Transparent)
    $bars = @(@{x = 2; d = $data.ram }, @{x = 18; d = $data.vram })
    foreach ($b in $bars) {
        $g.FillRectangle((New-Object Drawing.SolidBrush $COL.free), $b.x, 0, 12, 32)
        if (-not $data -or -not $b.d -or $b.d.total -le 0) { continue }
        $y = 32.0
        foreach ($p in $b.d.parts.PSObject.Properties) {
            $h = 32.0 * $p.Value / $b.d.total
            if ($h -le 0) { continue }
            $brush = New-Object Drawing.SolidBrush (Get-PartColor $p.Name $data.me)
            $g.FillRectangle($brush, [float]$b.x, [float]($y - $h), 12.0, [float]$h)
            $brush.Dispose()
            $y -= $h
        }
    }
    if (-not $data) { $g.FillRectangle((New-Object Drawing.SolidBrush $COL.dead), 2, 0, 28, 32) }
    $g.Dispose()
    $h = $bmp.GetHicon()
    $icon = [Drawing.Icon]::FromHandle($h).Clone()
    [void][TrayIconApi]::DestroyIcon($h)     # sem isso, 24h de atualizações vazam handles
    $bmp.Dispose()
    return $icon
}

function Format-Tip($data) {
    if (-not $data) { return "Monitor do servidor: sem contato`nclique para abrir o terminal" }
    $me = $data.me
    $lines = @("$($data.host) $($data.t) - CPU $([int]$data.cpu)%")
    $mine = 0.0
    foreach ($p in $data.ram.parts.PSObject.Properties) {
        $owner = ($p.Name -split '\|', 2)[0]
        if ($owner -eq $me -or $owner -like "*$me*") { $mine += $p.Value }
    }
    $lines += "RAM {0:n1}/{1:n0} GiB - voce {2:n1}" -f $data.ram.used, $data.ram.total, $mine
    if ($data.vram.total -gt 0) {
        $lines += "VRAM {0:n1}/{1:n0} GiB" -f $data.vram.used, $data.vram.total
    }
    if ($data.models.Count -gt 0) {
        $m = $data.models[0]
        $lines += "Ollama: {0} {1:n1} GiB ({2})" -f $m.name, $m.gib, $m.owner
    }
    $outros = @($data.people.PSObject.Properties | Where-Object { $_.Name -ne $me } | ForEach-Object { $_.Name })
    if ($outros.Count -gt 0) { $lines += "tambem logado: " + ($outros -join ", ") }
    $tip = $lines -join "`n"
    if ($tip.Length -gt 127) { $tip = $tip.Substring(0, 124) + "..." }
    return $tip
}

function Set-Tip($ni, [string]$text) {
    # NotifyIcon.Text trava em 63 caracteres; o campo privado aceita 127
    try {
        [Windows.Forms.NotifyIcon].GetField("text", "NonPublic,Instance").SetValue($ni, $text)
        [Windows.Forms.NotifyIcon].GetMethod("UpdateIcon", "NonPublic,Instance").Invoke($ni, @($true))
    } catch {
        $ni.Text = $text.Substring(0, [Math]::Min(62, $text.Length))
    }
}

# ---- conexão ---------------------------------------------------------------
$sshOpts = @("-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
             "-o", "ServerAliveInterval=20", "-o", "ServerAliveCountMax=3")
$script:proc = $null
$script:readTask = $null
$script:lastData = $null
$script:lastSeen = [DateTime]::MinValue
$script:nextTry = [DateTime]::MinValue

function Start-Feed {
    Stop-Feed
    $script:nextTry = (Get-Date).AddSeconds(20)
    # manda a versão atual do script antes de rodar
    $scp = Start-Process scp.exe -ArgumentList (@("-q", "-i", $Key) + $sshOpts + @($Script, "${Server}:.live_top.py")) `
                        -NoNewWindow -PassThru -Wait
    if ($scp.ExitCode -ne 0) { return }
    $psi = New-Object Diagnostics.ProcessStartInfo
    $psi.FileName = "ssh.exe"
    $psi.Arguments = (@("-i", "`"$Key`"") + $sshOpts + @($Server,
                      "`"python3 -u ~/.live_top.py --json --interval $Interval`"")) -join " "
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $script:proc = [Diagnostics.Process]::Start($psi)
    $script:readTask = $script:proc.StandardOutput.ReadLineAsync()
}

function Stop-Feed {
    if ($script:proc -and -not $script:proc.HasExited) { try { $script:proc.Kill() } catch {} }
    $script:proc = $null
    $script:readTask = $null
}

function Open-Monitor {
    # console clássico: preto, sólido, sem herdar tema nenhum do Windows Terminal
    Start-Process "$env:SystemRoot\System32\conhost.exe" -ArgumentList @("cmd.exe", "/c", "`"$Launcher`"")
}

function Open-MonitorWT {
    # perfil "Monitor Servidor" — só existe depois de fechar e reabrir o Windows Terminal
    if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
        Start-Process wt.exe -ArgumentList @("-w", "new", "-p", "Monitor Servidor")
    } else { Open-Monitor }
}

# ---- bandeja ---------------------------------------------------------------
$ni = New-Object Windows.Forms.NotifyIcon
$ni.Icon = New-TrayIcon $null
$ni.Visible = $true
Set-Tip $ni "Monitor do servidor: conectando..."

$menu = New-Object Windows.Forms.ContextMenuStrip
[void]$menu.Items.Add("Abrir monitor", $null, { Open-Monitor })
[void]$menu.Items.Add("Abrir no Windows Terminal", $null, { Open-MonitorWT })
[void]$menu.Items.Add("Reconectar agora", $null, { Start-Feed })
[void]$menu.Items.Add("-")
[void]$menu.Items.Add("Sair", $null, {
    $script:running = $false
    Stop-Feed
    $ni.Visible = $false
    $ni.Dispose()
    [Windows.Forms.Application]::Exit()
})
$ni.ContextMenuStrip = $menu
$ni.add_MouseClick({ if ($_.Button -eq [Windows.Forms.MouseButtons]::Left) { Open-Monitor } })

Start-Feed

$timer = New-Object Windows.Forms.Timer
$timer.Interval = 500
$timer.add_Tick({
    # linha nova pronta? (ReadLineAsync não bloqueia a interface)
    if ($script:readTask -and $script:readTask.IsCompleted) {
        $line = $script:readTask.Result
        if ($null -eq $line) {
            Stop-Feed                                   # conexão terminou
        } else {
            try {
                $d = $line | ConvertFrom-Json
                $script:lastData = $d
                $script:lastSeen = Get-Date
                $old = $ni.Icon
                $ni.Icon = New-TrayIcon $d
                if ($old) { $old.Dispose() }
                $tip = Format-Tip $d
                Set-Tip $ni $tip
                # espelho do tooltip em arquivo: serve para conferir que os dados chegam
                try { [IO.File]::WriteAllText("$env:TEMP\monitor_servidor_tip.txt", $tip) } catch {}
            } catch {}
            if ($script:proc -and -not $script:proc.HasExited) {
                $script:readTask = $script:proc.StandardOutput.ReadLineAsync()
            }
        }
    }
    # sem notícias há tempo demais: ícone apagado e nova tentativa
    $stale = ((Get-Date) - $script:lastSeen).TotalSeconds -gt ($Interval * 3 + 20)
    if ($stale -and $script:lastData) {
        $script:lastData = $null
        $old = $ni.Icon; $ni.Icon = New-TrayIcon $null; if ($old) { $old.Dispose() }
        Set-Tip $ni (Format-Tip $null)
    }
    if ((-not $script:proc -or $script:proc.HasExited) -and (Get-Date) -gt $script:nextTry) { Start-Feed }
})
$timer.Start()

[Windows.Forms.Application]::Run()
Stop-Feed
$ni.Dispose()
