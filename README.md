# SartoriusBridge

A lightweight desktop app that connects Sartorius precision scales to [Formulator](https://formulator.focalfinishes.com) and other web applications.

## Features

- Real-time weight streaming via WebSocket (port 8765)
- System tray/menu bar icon with connection status
- Auto-reconnect when scale is unplugged/reconnected
- Works with PMA Evolution and PMA Power series scales

---

## Windows

### Prerequisites

Install these before running SartoriusBridge:

| Requirement | Download | Notes |
|-------------|----------|-------|
| **Sartorius Driver** | [Driver PMA (ZIP)](https://www.sartorius.com/download/32264/22/driver-pma-data.zip) | Extract and run `Setup.bat` |
| **Python 3** | [python.org/downloads](https://www.python.org/downloads/) | Check "Add to PATH" during install |

### Installation

1. Download **SartoriusBridge.exe** from [Releases](https://github.com/briandperla/SartoriusBridge/releases)
2. Double-click to run
3. Look for the scale icon in the system tray (bottom-right corner)
4. Right-click the icon for menu options

### Verifying the Driver

After installing the Sartorius driver:
1. Connect your scale via USB
2. Open **Device Manager**
3. Look under **Ports (COM & LPT)** for "Sartorius" or a new COM port

### Troubleshooting

**Scale not detected?**
- Ensure the Sartorius Driver PMA is installed
- Check Device Manager for the COM port
- Restart the app after connecting the scale

**Using X-Pert Formula Management?**
- X-Pert locks the COM port exclusively
- Close X-Pert before using SartoriusBridge
- Power cycle the scale after closing X-Pert

---

## macOS

### Prerequisites

Install these before running SartoriusBridge:

| Requirement | Install Command | Notes |
|-------------|-----------------|-------|
| **Homebrew** | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` | [brew.sh](https://brew.sh) |
| **libusb** | `brew install libusb` | Required for USB communication |
| **Python 3** | `brew install python` | Usually pre-installed on newer Macs |

### Installation

1. Download **SartoriusBridge.dmg** from [Releases](https://github.com/briandperla/SartoriusBridge/releases)
2. Open the DMG and drag **SartoriusBridge** to Applications
3. Right-click the app and select **Open** (required first time for Gatekeeper)
4. A notification confirms the app is active
5. The scale icon appears in your menu bar

### Troubleshooting

**"libusb not available"**
- Run `brew install libusb` in Terminal

**App won't open (Gatekeeper)**
- Right-click the app → **Open** → Click **Open** in the dialog

**Scale not found**
- Ensure libusb is installed
- Check that the scale is connected via USB

---

## Status Icons

The tray/menu bar icon indicates connection status:

| Icon | Meaning |
|------|---------|
| 🟢 **Green** | Scale connected and streaming |
| 🟡 **Yellow** | Server running, waiting for scale |
| ⚫ **Gray** | Server stopped |

---

## Menu Options

Right-click (Windows) or click (macOS) the icon for these options:

- **Start Server** – Start the WebSocket bridge
- **Stop Server** – Stop the bridge
- **Open Formulator** – Launch the Formulator web app
- **Quit** – Stop server and exit

---

## Supported Scales

| Model | USB VID | USB PID | Connection Type |
|-------|---------|---------|-----------------|
| Sartorius PMA Evolution | `0x24BC` | `0x2010` | Native USB |
| Sartorius PMA Power | `0x0403` | `0x6001` | FTDI FT232 |

**Serial Settings:** 9600 baud, 8N1, no handshake, DTR/RTS high

---

## For Developers

### WebSocket API

Connect to `ws://localhost:8765` to receive weight data.

**Server Messages:**
```json
{ "type": "status", "connected": true }
{ "type": "weight", "data": { "weight": 123.4, "unit": "g" } }
```

**Client Commands:**
```json
{ "command": "tare" }
{ "command": "read" }
```

### Building from Source

**macOS:**
```bash
pip3 install pyinstaller pyusb websockets rumps pyobjc
pyinstaller --clean -y SartoriusBridge_mac.spec
```

**Windows:**
```cmd
pip install pyserial websockets pystray pillow pyinstaller
pyinstaller --clean -y SartoriusBridge_windows.spec
```

---

## License

Proprietary – Focal Finishes LLC
