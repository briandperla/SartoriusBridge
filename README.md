# SartoriusBridge

A cross-platform app that bridges Sartorius PMA precision scales to web browsers via WebSocket.

## Overview

SartoriusBridge enables real-time weight data from Sartorius scales to be captured in web applications. It runs as a lightweight system tray/menu bar app and provides:

- **WebSocket server** on port 8765 for real-time weight streaming
- **HTTP interface** on port 8080 for standalone testing
- **Auto-reconnect** when scale is disconnected/reconnected
- **Multi-scale support** for PMA Evolution and PMA Power series

## Download

Download the latest release from the [Releases](https://github.com/briandperla/SartoriusBridge/releases) page:
- **macOS**: `SartoriusBridge.dmg`
- **Windows**: `SartoriusBridge.exe`

---

## Windows Installation

### Step 1: Install the Sartorius Driver

1. Download [Driver PMA](https://www.sartorius.com/download/32264/22/driver-pma-data.zip) (2.2 MB ZIP)
2. Extract and run `Setup.bat` to install
3. This creates a Virtual COM Port for your scale
4. Verify: Open Device Manager and look for the scale under "Ports (COM & LPT)"

### Step 2: Run SartoriusBridge

1. Download `SartoriusBridge.exe` from Releases
2. Double-click to run
3. Look for the scale icon in the system tray (bottom-right)
4. Right-click for menu options

### Windows Troubleshooting

**Scale not detected?**
- Ensure the Sartorius "Driver PMA" is installed
- Check Device Manager for the COM port
- Run `test_scale_windows.py` to diagnose

**Using X-Pert Formula Management?**
- X-Pert holds the COM port open and may stop the scale from streaming data
- Close X-Pert before using SartoriusBridge
- Power cycle the scale (turn off, then on) after closing X-Pert
- The two applications cannot use the scale simultaneously

---

## macOS Installation

### Requirements
- macOS 10.13 or later
- Homebrew (for libusb): `brew install libusb`

### Option 1: Pre-built App

1. Download `SartoriusBridge.dmg` from Releases
2. Open the DMG and drag to Applications
3. Right-click and select **Open** (required first time for Gatekeeper)

### Option 2: Run from Source

```bash
# Install dependencies
brew install libusb
pip3 install pyusb websockets rumps

# Run the menu bar app
python3 sartorius_menubar.py
```

### macOS Troubleshooting

**"libusb not available"**: Run `brew install libusb`

**Permission denied**: Right-click the app and select **Open** to bypass Gatekeeper

---

## Usage

### System Tray/Menu Bar

When running, you'll see a scale icon in your system tray (Windows) or menu bar (macOS):

| Icon | Status |
|------|--------|
| Gray | Server running, waiting for scale |
| Green | Server running, scale connected |
| Yellow | Server starting |

**Menu Options:**
- **Start Server** - Starts the WebSocket bridge
- **Stop Server** - Stops the bridge
- **Open Test Page** - Opens http://localhost:8080
- **Open Formulator** - Opens the Formulator app
- **Quit** - Stops server and exits

### Standalone Server

For testing or headless operation:

```bash
# macOS
python3 sartorius_web_server.py

# Windows
python sartorius_web_server_windows.py
```

Then open http://localhost:8080 in your browser.

---

## WebSocket API

Connect to `ws://localhost:8765` to receive weight data.

### Messages from Server

```javascript
// Connection status
{ "type": "status", "connected": true/false, "weight": {...} }

// Weight reading
{ "type": "weight", "data": { "weight": 123.4, "unit": "g", "raw": "..." } }

// Command acknowledgment
{ "type": "ack", "command": "tare" }
```

### Commands to Server

```javascript
// Tare the scale
{ "command": "tare" }

// Zero the scale
{ "command": "zero" }

// Request weight reading
{ "command": "read" }
```

---

## Compatible Hardware

| Scale | USB VID | USB PID | Connection |
|-------|---------|---------|------------|
| Sartorius PMA Evolution | 0x24BC | 0x2010 | USB (Sartorius native) |
| Sartorius PMA Power | 0x0403 | 0x6001 | USB (FTDI FT232) |

### Required Scale Settings

Both scales should be configured with these serial settings:
- **Baud Rate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Handshake:** None

---

## Files

| File | Platform | Description |
|------|----------|-------------|
| `sartorius_menubar.py` | macOS | Menu bar app wrapper |
| `sartorius_web_server.py` | macOS | WebSocket server (pyusb) |
| `sartorius_tray_windows.py` | Windows | System tray app wrapper |
| `sartorius_web_server_windows.py` | Windows | WebSocket server (pyserial) |
| `sartorius_scale_windows.py` | Windows | Scale communication via COM port |
| `test_scale.py` | macOS | Diagnostic script |
| `test_scale_windows.py` | Windows | Diagnostic script |

---

## Building from Source

### macOS

```bash
pip3 install py2app
python3 setup.py py2app
```

### Windows

```cmd
build_windows.bat
```

Or manually:

```cmd
pip install pyserial websockets pystray pillow pyinstaller
pyinstaller --clean -y SartoriusBridge_windows.spec
```

The executable will be at `dist\SartoriusBridge.exe`

---

## License

Proprietary - Focal Finishes LLC
