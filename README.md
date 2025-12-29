# SartoriusBridge

A macOS app that bridges Sartorius PMA precision scales to web browsers via WebSocket.

## Overview

SartoriusBridge enables real-time weight data from Sartorius scales to be captured in web applications. It runs as a lightweight app on macOS and provides:

- **WebSocket server** on port 8765 for real-time weight streaming
- **HTTP interface** on port 8080 for standalone testing
- **Auto-reconnect** when scale is disconnected/reconnected
- **Multi-scale support** for PMA Evolution and PMA Power series

## Requirements

### macOS
- macOS 10.13 or later
- Python 3.8+
- Homebrew (for libusb)

### Python Dependencies
```bash
pip3 install pyusb websockets rumps
```

### System Dependencies
```bash
brew install libusb
```

## Installation

### Option 1: Run from Source

```bash
# Clone the repository
git clone https://github.com/briandperla/SartoriusBridge.git
cd SartoriusBridge

# Install dependencies
pip3 install pyusb websockets rumps
brew install libusb

# Run the menu bar app
python3 sartorius_menubar.py
```

### Option 2: Use Pre-built App

1. Download `SartoriusBridge.app` from Releases
2. Move to `/Applications`
3. Right-click and select **Open** (required first time for security)

## Usage

### Menu Bar App

When running, you'll see a scale icon (⚖️) in your menu bar:

| Icon | Status |
|------|--------|
| ⚖️ | Server running, waiting for scale |
| ⚖️✓ | Server running, scale connected |
| ⚖️✗ | Server stopped |

**Menu Options:**
- **Start Server** - Starts the WebSocket bridge
- **Stop Server** - Stops the bridge
- **Open Formulator** - Opens http://localhost:3000
- **Quit** - Stops server and exits

### Standalone Server

For testing or headless operation:

```bash
python3 sartorius_web_server.py
```

Then open http://localhost:8080 in your browser.

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

## Compatible Hardware

| Scale | USB VID | USB PID | Chip |
|-------|---------|---------|------|
| Sartorius PMA Evolution | 0x24BC | 0x2010 | Sartorius native |
| Sartorius PMA Power | 0x0403 | 0x6001 | FTDI FT232 |

### Required Scale Settings
Both scales must be configured with these serial settings:
- **Baud Rate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Handshake:** None

## Files

| File | Description |
|------|-------------|
| `sartorius_menubar.py` | macOS menu bar app wrapper |
| `sartorius_web_server.py` | WebSocket/HTTP server with scale communication |

## Building the App Bundle

To create a standalone `.app`:

```bash
# Install py2app
pip3 install py2app

# Create setup.py (see below) and run:
python3 setup.py py2app
```

## Troubleshooting

### "libusb not available"
Ensure libusb is installed: `brew install libusb`

### Scale not detected
1. Check USB connection
2. Ensure scale is powered on
3. Verify USB VID/PID matches (use `system_profiler SPUSBDataType`)

### Permission denied on macOS
Right-click the app and select **Open** to bypass Gatekeeper.

## License

Proprietary - Focal Finishes LLC
