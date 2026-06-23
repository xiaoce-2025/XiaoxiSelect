@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo    PKU Auto-Elective - Build Script
echo ============================================================
echo.

set CONDA_ENV=aibasis
set CONDA_PATH=D:\Anaconda3
set PROJECT_DIR=%~dp0
set DIST_DIR=%PROJECT_DIR%dist\gui_main

echo [1/6] Activating Conda environment: %CONDA_ENV%
call "%CONDA_PATH%\Scripts\activate.bat" %CONDA_ENV%
if errorlevel 1 (
    echo ERROR: Failed to activate Conda environment
    pause
    exit /b 1
)
echo       OK

echo.
echo [2/6] Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo       Installing PyInstaller...
    pip install pyinstaller -q
)
python -c "import PyInstaller; print('       PyInstaller ' + PyInstaller.__version__)"

echo.
echo [3/6] Cleaning old build artifacts...
if exist "%PROJECT_DIR%build" rd /s /q "%PROJECT_DIR%build"
if exist "%PROJECT_DIR%dist" rd /s /q "%PROJECT_DIR%dist"
echo       Done

echo.
echo [4/6] Running PyInstaller (this may take 1-3 minutes)...
cd /d "%PROJECT_DIR%"

for /f "delims=" %%i in ('python -c "from PyQt6.QtCore import QLibraryInfo; print(QLibraryInfo.path(QLibraryInfo.LibraryPath.BinsPath))"') do set QT_BIN_PATH=%%i

pyinstaller --noconfirm --onedir --windowed --name "PKUElective" --icon "myico.ico" --path "%QT_BIN_PATH%" --add-data "autoelective/models;autoelective/models" --add-data "pictures;pictures" --add-data "assets;assets" --add-data "user_agents.txt.gz;." --add-data "config.ini.template;." --add-data "apikey.json.template;." --hidden-import "autoelective.captcha.online" --hidden-import "handlers.log_server" --hidden-import "handlers.gui_log_handler" --exclude-module "torch.cuda" --exclude-module "torch.distributed" --exclude-module "torch._C._dynamo" --exclude-module "torch._inductor" --exclude-module "torch._functorch" --exclude-module "torch._export" --exclude-module "torch.onnx" --exclude-module "torchvision" --exclude-module "torch.backends.cuda" --exclude-module "torch.backends.cudnn" --exclude-module "torch.backends.mps" --exclude-module "torch.ao" --exclude-module "torch.testing" --exclude-module "torch.utils.tensorboard" --exclude-module "torch.utils.benchmark" --exclude-module "torch.profiler" --exclude-module "flask" --exclude-module "Werkzeug" gui_main.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed
    pause
    exit /b 1
)
echo       Done

echo.
echo [5/6] Post-build cleanup and config init...

REM Delete torch static libraries (not needed at runtime)
for /r "%DIST_DIR%\_internal\torch\lib" %%f in (*.lib) do del /q "%%f" 2>nul
for /r "%DIST_DIR%\_internal\torch\lib" %%f in (*.lib) do del /q "%%f" 2>nul

REM Delete torch headers
if exist "%DIST_DIR%\_internal\torch\include" rd /s /q "%DIST_DIR%\_internal\torch\include" 2>nul

REM Delete torch test data
if exist "%DIST_DIR%\_internal\torch\test" rd /s /q "%DIST_DIR%\_internal\torch\test" 2>nul

REM Delete __pycache__
for /r "%DIST_DIR%" %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d" 2>nul

REM Copy config templates
if not exist "%DIST_DIR%\config.ini" (
    copy "%PROJECT_DIR%config.ini.template" "%DIST_DIR%\config.ini" >nul
    echo       Generated config.ini from template
) else (
    echo       config.ini already exists, skipped
)

if not exist "%DIST_DIR%\apikey.json" (
    copy "%PROJECT_DIR%apikey.json.template" "%DIST_DIR%\apikey.json" >nul
    echo       Generated apikey.json from template
) else (
    echo       apikey.json already exists, skipped
)

REM Create runtime directories
if not exist "%DIST_DIR%\cache\captcha" mkdir "%DIST_DIR%\cache\captcha"
if not exist "%DIST_DIR%\log\error" mkdir "%DIST_DIR%\log\error"
if not exist "%DIST_DIR%\log\request" mkdir "%DIST_DIR%\log\request"
if not exist "%DIST_DIR%\log\web" mkdir "%DIST_DIR%\log\web"
echo       Created cache/ and log/ directories

REM Create launcher script
(
echo @echo off
echo cd /d "%%~dp0"
echo start "" "PKUElective.exe"
) > "%DIST_DIR%\Launch.bat"
echo       Created Launch.bat

echo.
echo [6/6] Build complete!
echo.
echo ============================================================
echo    Output: %DIST_DIR%
echo.
echo    PKUElective.exe    - Main program
echo    Launch.bat         - Double-click to start
echo    config.ini         - Config file (from template)
echo    apikey.json        - Captcha API key
echo    autoelective/models/ - CNN models
echo    cache/             - Runtime cache
echo    log/               - Log files
echo ============================================================
echo.

explorer "%DIST_DIR%"
pause
