@echo off
cd /d "%~dp0"
echo =======================================================
echo   SartoriusBridge Windows Build Script
echo =======================================================
echo.
echo Working directory: %cd%
echo.

echo Installing dependencies...
pip install pyserial websockets pystray pillow pyinstaller

echo.
echo Building SartoriusBridge.exe...
echo Looking for spec file...
dir SartoriusBridge_windows.spec
echo.
python -m PyInstaller --clean -y "%~dp0SartoriusBridge_windows.spec"

echo.
if exist "dist\SartoriusBridge.exe" (
    echo =======================================================
    echo   BUILD SUCCESSFUL!
    echo =======================================================
    echo.
    echo Your executable is at: dist\SartoriusBridge.exe
    echo.
    echo To upload to GitHub release, run:
    echo   gh release upload v1.0.0 dist\SartoriusBridge.exe
) else (
    echo =======================================================
    echo   BUILD FAILED
    echo =======================================================
    echo Check the errors above.
)

echo.
pause
