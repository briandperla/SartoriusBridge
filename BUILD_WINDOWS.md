# Building SartoriusBridge for Windows

## Prerequisites

1. **Install Python 3.9+** from https://python.org
   - Check "Add Python to PATH" during installation

2. **Install the Sartorius Driver** (for testing)
   - Download [Driver PMA](https://www.sartorius.com/download/32264/22/driver-pma-data.zip) (2.2 MB ZIP)
   - Extract and run `Setup.bat` to install
   - This creates a Virtual COM Port for scale communication
   - No additional drivers (like Zadig) are required

3. **Install Python dependencies**:
   ```cmd
   pip install pyserial websockets pystray pillow pyinstaller
   ```

## Build Steps

### Option 1: Use the Build Script

Simply run:
```cmd
build_windows.bat
```

### Option 2: Manual Build

1. Open Command Prompt in the SartoriusBridge folder

2. Run PyInstaller:
   ```cmd
   pyinstaller --clean -y SartoriusBridge_windows.spec
   ```

3. The executable will be in: `dist\SartoriusBridge.exe`

## Testing

1. Ensure the Sartorius driver is installed
2. Plug in the Sartorius scale
3. Run `dist\SartoriusBridge.exe`
4. Look for the scale icon in the system tray
5. Open http://localhost:8080 to test

## Distribution

The single `SartoriusBridge.exe` file can be distributed to users.

Users need:
- The Sartorius "Driver PMA" installed (creates COM port)
- No additional DLLs or drivers required

## Troubleshooting

- **Scale not detected**: Install the Sartorius "Driver PMA" driver
- **Permission errors**: Run as Administrator
- **Build errors**: Ensure all dependencies are installed with pip

## Architecture Note

The Windows version uses `pyserial` to communicate via COM port:
- `sartorius_scale_windows.py` - Scale communication class
- `sartorius_web_server_windows.py` - WebSocket server
- `sartorius_tray_windows.py` - System tray app

This is different from macOS which uses `pyusb` for direct USB access.
