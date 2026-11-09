@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo        Iniciando Servidor Flask - Meus Jogos
echo ========================================================
echo.
echo Acesse no seu navegador: http://localhost:5000
echo Pressione Ctrl+C para encerrar o servidor.
echo.

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py run.py
    goto fim
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python run.py
    goto fim
)

if exist "C:\Users\VINICIUSSANTANASANTO\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
    "C:\Users\VINICIUSSANTANASANTO\AppData\Local\Python\pythoncore-3.14-64\python.exe" run.py
    goto fim
)

echo [ERRO] Python nao foi localizado. Verifique a instalacao.
pause
exit /b 1

:fim
pause

