@echo off
echo Iniciando aplicacion BootCasosV2...
echo.

REM Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call .venv\Scripts\activate.bat
)

REM Instalar navegadores de Playwright si es necesario
echo Verificando navegadores de Playwright...
python -c "import playwright; print('Playwright disponible')" 2>nul
if errorlevel 1 (
    echo Instalando navegadores de Playwright...
    playwright install
)

REM Ejecutar la aplicacion
echo Ejecutando aplicacion...
python main.py

pause