# Building SartoriusBridge for Windows

## Prerequisites

1. **Install Python 3.9+** from https://python.org
   - Check "Add Python to PATH" during installation

2. **Install libusb** (required for USB scale communication):
   - Download from: https://github.com/libusb/libusb/releases
   - Extract `libusb-1.0.dll` to `C:\Windows\System32\`
   - OR use Zadig (https://zadig.akeo.ie/) to install the driver for your scale

3. **Install Python dependencies**:
   ```cmd
   pip install pyusb websockets pystray pillow pyinstaller
   ```

## Build Steps

1. Open Command Prompt in the SartoriusBridge folder

2. Run PyInstaller:
   ```cmd
   pyinstaller --clean -y SartoriusBridge_windows.spec
   ```

3. The executable will be in: `dist\SartoriusBridge.exe`

## Testing

1. Plug in the Sartorius scale
2. Run `dist\SartoriusBridge.exe`
3. Look for the scale icon in the system tray
4. Open http://localhost:8080 to test

## Distribution

The single `SartoriusBridge.exe` file can be distributed to users.
Users will still need libusb-1.0.dll installed (or bundled alongside).

## Troubleshooting

- **Scale not detected**: Install libusb driver using Zadig
- **Permission errors**: Run as Administrator
- **Missing DLL errors**: Ensure libusb-1.0.dll is in System32 or same folder as exe
