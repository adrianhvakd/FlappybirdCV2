@echo off
setlocal
cd /d "%~dp0\.."

set APP=FlappyBirdVision
set VENV=.build-venv

echo ==^> 1/4 Creando entorno de compilacion (%VENV%)
python -m venv %VENV%
if errorlevel 1 goto :error

%VENV%\Scripts\python -m pip install --upgrade pip -q
%VENV%\Scripts\pip install -q -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo ==^> 2/4 Compilando con PyInstaller
%VENV%\Scripts\pyinstaller --clean --noconfirm packaging\flappybird.spec
if errorlevel 1 goto :error

echo ==^> 3/4 Generando instalador (si hay Inno Setup)
where ISCC >nul 2>nul
if %errorlevel%==0 (
    ISCC packaging\windows_installer.iss
    if errorlevel 1 goto :error
    echo     -^> dist\FlappyBirdVision-Setup.exe
) else (
    echo     [!] Inno Setup ^(ISCC^) no encontrado. Solo se genero dist\%APP%\
    echo         Instala Inno Setup desde https://jrsoftware.org/isdl.php
)

echo ==^> 4/4 Listo
echo Ejecuta: dist\%APP%\%APP%.exe
exit /b 0

:error
echo.
echo *** Error durante la compilacion ***
exit /b 1
