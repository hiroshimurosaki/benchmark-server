@echo off
REM Sincronizador do dashboard b3: puxa os arquivos do servidor pro PC a cada 15s.
REM Duplo-clique e deixe a janela aberta num canto enquanto o benchmark roda.
REM Escreve em .tmp e renomeia (atomico) pro dashboard nunca ler arquivo pela metade.
REM
REM Depois de abrir: no dashboard_b3.html clique em "Acompanhar ao vivo" e
REM escolha a pasta b3\live. A pagina passa a recarregar sozinha.
setlocal
if defined B3_HOST (set HOST=%B3_HOST%) else (set HOST=fernando.murusaki@10.10.10.151)
set KEY=%USERPROFILE%\.ssh\id_benchmark
set REMOTE=~/benchmark/b3
set LIVE=%~dp0b3\live

if not exist "%LIVE%" mkdir "%LIVE%"

echo Sincronizando %HOST%:%REMOTE%  ->  %LIVE%
echo (feche esta janela para parar)
echo.
:loop
call :pull relatorio_b3.json
call :pull results_b3.jsonl
call :pull index_bench.json
timeout /t 15 /nobreak >nul
goto loop

:pull
scp -P 22 -i "%KEY%" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes ^
    %HOST%:%REMOTE%/%1 "%LIVE%\%1.tmp" 2>nul
if exist "%LIVE%\%1.tmp" (
  move /y "%LIVE%\%1.tmp" "%LIVE%\%1" >nul
  echo [%TIME%] %1 atualizado
) else (
  echo [%TIME%] %1 -- falha ^(servidor fora? chave? arquivo ainda nao existe?^)
)
exit /b
