# Instala o monitor do servidor neste PC:
#   1. perfil "Monitor Servidor" no Windows Terminal (fundo preto, sem transparência),
#      como fragmento — o seu settings.json não é tocado;
#   2. ícone na bandeja, que sobe junto com o Windows (atalho na pasta Inicializar);
#   3. liga a bandeja agora.
# Desfaz tudo com:  powershell -ExecutionPolicy Bypass -File instalar_monitor.ps1 -Desinstalar
param([switch]$Desinstalar)

$ErrorActionPreference = "Stop"
$root     = $PSScriptRoot
$frag     = "$env:LOCALAPPDATA\Microsoft\Windows Terminal\Fragments\MonitorServidor"
$startup  = [Environment]::GetFolderPath("Startup")
$atalho   = "$startup\Monitor Servidor.lnk"
$tray     = "$root\tray_monitor.ps1"

function Stop-Tray {
    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
        Where-Object { $_.CommandLine -like "*tray_monitor.ps1*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

if ($Desinstalar) {
    Stop-Tray
    Remove-Item $frag -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $atalho -Force -ErrorAction SilentlyContinue
    Write-Host "Removido: perfil do Windows Terminal, atalho de inicialização e ícone da bandeja."
    return
}

# 1. perfil do Windows Terminal (com o caminho real desta pasta)
New-Item -ItemType Directory -Force -Path $frag | Out-Null
$json = Get-Content "$root\monitor_terminal.json" -Raw -Encoding UTF8
$json = $json.Replace('%USERPROFILE%\\benchmark-server\\infra\\monitor\\monitor_servidor.bat',
                      ("$root\monitor_servidor.bat").Replace('\', '\\'))
[IO.File]::WriteAllText("$frag\monitor.json", $json, (New-Object Text.UTF8Encoding $false))
Write-Host "Perfil 'Monitor Servidor' instalado em $frag"

# 2. atalho na pasta Inicializar (janela escondida)
Stop-Tray
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut($atalho)
$lnk.TargetPath  = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$lnk.Arguments   = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$tray`""
$lnk.WorkingDirectory = $root
$lnk.WindowStyle = 7          # minimizado, sem piscar console
$lnk.Description = "Monitor do servidor ianode na bandeja"
$lnk.Save()
Write-Host "Atalho de inicialização criado em $atalho"

# 3. sobe a bandeja agora
Start-Process powershell.exe -WindowStyle Hidden `
    -ArgumentList @("-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", "`"$tray`"")
Write-Host "Ícone da bandeja ligado. A primeira leitura chega em alguns segundos."
Write-Host "Clique no ícone para abrir o monitor completo; botão direito tem 'Sair'."
