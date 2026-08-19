@echo off
REM Sincronizador do dashboard: puxa dashboard_b1.json do servidor pro PC a cada 15s.
REM Abra este arquivo (duplo-clique) e deixe a janela aberta num canto enquanto o benchmark roda.
REM Escreve em arquivo temporario e renomeia (atomico) pra o dashboard nunca ler json pela metade.
setlocal
set HOST=nicolas.benedetti@10.10.10.151
set KEY=%USERPROFILE%\.ssh\id_benchmark
set DEST=%~dp0dashboard_b1.json
set TMP=%~dp0dashboard_b1.json.tmp

echo Sincronizando %HOST%:~/benchmark/dashboard_b1.json  ->  %DEST%
echo (feche esta janela para parar)
echo.
:loop
scp -P 22 -i "%KEY%" -o StrictHostKeyChecking=no -o ConnectTimeout=10 %HOST%:~/benchmark/dashboard_b1.json "%TMP%" 2>nul
if exist "%TMP%" (
  move /y "%TMP%" "%DEST%" >nul
  echo [%TIME%] atualizado
) else (
  echo [%TIME%] falha ao puxar ^(servidor fora? chave?^)
)
timeout /t 15 /nobreak >nul
goto loop
