@echo off
REM Monitor ao vivo do servidor: barras de RAM/VRAM por dono, modelos carregados, pessoas.
REM Duplo-clique e deixe a janela aberta. Ctrl+C (ou fechar a janela) para sair.
REM Copia o script para o servidor a cada abertura (sempre a versao atual) e abre com
REM ssh -tt: o terminal remoto e o que deixa o monitor caber certinho na janela.
chcp 65001 >nul
title Monitor do servidor ianode
REM no console classico da janela fica do tamanho certo; no Windows Terminal isso e ignorado
if not defined WT_SESSION mode con: cols=112 lines=32
setlocal
if defined B3_HOST (set HOST=%B3_HOST%) else (set HOST=fernando.murusaki@10.10.10.151)
set KEY=%USERPROFILE%\.ssh\id_benchmark
set SCRIPT=%~dp0live_top.py
set OPTS=-o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes -o ServerAliveInterval=15
set INTERVAL=2

:loop
scp -q -i "%KEY%" %OPTS% "%SCRIPT%" %HOST%:.live_top.py
ssh -tt -i "%KEY%" %OPTS% %HOST% "python3 -u ~/.live_top.py --interval %INTERVAL%"
echo.
echo [%TIME%] conexao caiu -- reconectando em 5s (feche a janela para parar)
timeout /t 5 /nobreak >nul
goto loop
