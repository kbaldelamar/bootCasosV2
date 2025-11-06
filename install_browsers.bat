@echo off
echo Instalando navegadores de Playwright...
echo.

REM Activar el entorno virtual
call .venv\Scripts\activate.bat

REM Instalar navegadores de Playwright
playwright install

echo.
echo Instalacion completada!
echo.
pause