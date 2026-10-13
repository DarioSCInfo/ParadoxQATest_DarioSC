@echo off
setlocal EnableExtensions

set "REPO_ROOT=%~dp0"
set "PYTHON_EXE="
set "PYTHON_ARGS="
set "VENV_PYTHON=%REPO_ROOT%.venv\Scripts\python.exe"

rem Reuse an installed Python 3.10+ when available.
where py.exe >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py.exe"
        set "PYTHON_ARGS=-3"
    )
)

if not defined PYTHON_EXE (
    where python.exe >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
        if not errorlevel 1 set "PYTHON_EXE=python.exe"
    )
)

rem Install Python 3.12 per-user if no suitable interpreter is present.
if not defined PYTHON_EXE (
    where winget.exe >nul 2>&1
    if errorlevel 1 (
        echo No se encontro Python 3.10+ ni winget.
        echo Instala Python 3.12 desde https://www.python.org/downloads/windows/ y vuelve a ejecutar setup.cmd.
        exit /b 1
    )
    echo Instalando Python 3.12 para este usuario...
    winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo No se pudo instalar Python con winget. Instala Python 3.12 manualmente y vuelve a ejecutar setup.cmd.
        exit /b 1
    ) else (
        py -3.12 -c "import sys; print(sys.version)" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=py.exe"
            set "PYTHON_ARGS=-3.12"
        )
    )
    if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
)

if not defined PYTHON_EXE (
    echo Python se instalo, pero no se encontro su ejecutable. Cierra y vuelve a abrir CMD, y ejecuta setup.cmd de nuevo.
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo Creando el entorno virtual del proyecto...
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%REPO_ROOT%.venv"
    if errorlevel 1 exit /b 1
)

echo Instalando pytest, Playwright y el complemento pytest-playwright...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%VENV_PYTHON%" -m pip install -r "%REPO_ROOT%requirements.txt"
if errorlevel 1 exit /b 1

echo Descargando Chromium para Playwright...
"%VENV_PYTHON%" -m playwright install chromium
if errorlevel 1 exit /b 1

echo.
echo Instalacion completada.
echo Ya puedes ejecutar tus automatizaciones con el comando habitual.
exit /b 0
