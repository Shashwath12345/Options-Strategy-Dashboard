@echo off
setlocal
cd /d "%~dp0"
echo Installing project dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)
echo Building standalone application...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OptionsStrategySimulator main.py
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
echo SUCCESS: dist\OptionsStrategySimulator.exe
pause
