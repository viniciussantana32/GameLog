@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo    Instalando Dependencias - Meus Jogos (JOGOSSALVOS)
echo ========================================================
echo.

where pip >nul 2>nul
if %ERRORLEVEL% equ 0 (
    pip install -r requirements.txt
    goto fim
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -m pip install -r requirements.txt
    goto fim
)

if exist "C:\Users\VINICIUSSANTANASANTO\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
    "C:\Users\VINICIUSSANTANASANTO\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pip install -r requirements.txt
    goto fim
)

echo [ERRO] Nao foi possivel encontrar o Python ou Pip no sistema.
pause
exit /b 1

:fim
echo.
echo ========================================================
echo  Dependencias instaladas com sucesso!
echo  Para iniciar o site, execute: .\iniciar.bat
echo ========================================================
pause

