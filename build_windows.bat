@echo off
cd /d "%~dp0"
echo =======================================================
echo   SartoriusBridge Windows Build Script
echo =======================================================
echo.
echo Working directory: %cd%
echo.

echo Installing dependencies...
pip install pyusb websockets pystray pillow pyinstaller

echo.
echo Building SartoriusBridge.exe...
pyinstaller --clean -y SartoriusBridge_windows.spec

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
