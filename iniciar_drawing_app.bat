@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv-local\Scripts\python.exe" (
    echo No se encontro el entorno virtual .venv-local.
    echo Ejecuta primero la instalacion de dependencias del proyecto.
    pause
    exit /b 1
)

".venv-local\Scripts\python.exe" "main.py"

if errorlevel 1 (
    echo.
    echo La aplicacion termino con un error.
    pause
)

endlocal