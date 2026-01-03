# SartoriusBridge Troubleshooting Guide

## macOS Issues

### Issue: Scale Shows "Connected" But No Weight Values

#### Symptoms
- Terminal shows "Scale connected!"
- Web interface (localhost:8080) shows "Scale Connected"
- But weight values never appear / stay blank
- WebSocket returns `weight: None`

#### Root Cause
The **PMA Evolution scale** (VID: 0x24BC, PID: 0x2010) internally uses an FTDI-style USB-to-serial chip, even though it has Sartorius vendor/product IDs.

Without proper serial configuration, the scale only sends 2-byte status packets (`\x01\x60`) instead of actual weight data.

#### The Fix
The scale requires FTDI serial configuration commands before it will transmit weight data:

```python
# These control transfers configure the internal FTDI chip:
self.dev.ctrl_transfer(0x40, 0x00, 0, 0, None)      # Reset
self.dev.ctrl_transfer(0x40, 0x03, 0x4138, 0, None) # Baud rate: 9600
self.dev.ctrl_transfer(0x40, 0x04, 0x0008, 0, None) # Data format: 8N1
self.dev.ctrl_transfer(0x40, 0x02, 0, 0, None)      # Flow control: none
self.dev.ctrl_transfer(0x40, 0x01, 0x0303, 0, None) # DTR/RTS high
self.dev.ctrl_transfer(0x40, 0x09, 16, 0, None)     # Latency timer
```

This is already included in `sartorius_web_server.py` for ALL scale types.

### Safari doesn't work
- **Cause:** Safari blocks `ws://localhost` from HTTPS pages (mixed content)
- **Fix:** Use Chrome instead

### macOS app doesn't open Terminal
- **Cause:** App bundle needs to use `os.system()` not `subprocess.run()` for the `open` command
- **Fix:** Already fixed in current version

### "libusb not available"
- **Fix:** Install libusb: `brew install libusb`

### Permission denied on macOS
- Right-click the app and select **Open** to bypass Gatekeeper

---

## Windows Issues

### Issue: "No scale detected"

#### Cause
The Sartorius driver is not installed, so Windows doesn't recognize the scale as a COM port.

#### Fix
1. Download and install "Driver PMA" from Sartorius website
2. After installation, the scale will appear as a COM port in Device Manager
3. Look under "Ports (COM & LPT)" for something like "USB Serial Port (COM3)"

### Issue: Scale connected but no weight values

#### Possible Causes
1. Wrong baud rate on scale
2. Scale not configured for continuous output

#### Fix
Check your scale's menu settings:
- **Baud Rate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Handshake:** None

Try pressing the PRINT button on the scale to manually send a weight reading.

### Issue: COM port in use

#### Cause
Another application is using the scale's COM port.

#### Fix
1. Close any other software that might be using the scale
2. Check Device Manager to identify which COM port the scale is on
3. Restart SartoriusBridge

---

## Diagnostic Tools

### macOS
Run the test script to verify scale communication:
```bash
python3 test_scale.py
```

### Windows
Run the Windows test script:
```cmd
python test_scale_windows.py
```

This will:
1. List all COM ports
2. Auto-detect the scale
3. Attempt to read weight data
4. Report success or failure

---

## Files Overview

| File | Location | Purpose |
|------|----------|---------|
| SartoriusBridge.app | /Applications/ | macOS menu bar app |
| SartoriusBridge.exe | Download folder | Windows system tray app |
| sartorius_web_server.py | Source folder | macOS WebSocket server |
| sartorius_web_server_windows.py | Source folder | Windows WebSocket server |
| test_scale.py | Source folder | macOS diagnostic |
| test_scale_windows.py | Source folder | Windows diagnostic |

---

## Getting Help

If issues persist, check the GitHub repo: https://github.com/briandperla/SartoriusBridge
