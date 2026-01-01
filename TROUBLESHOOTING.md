# SartoriusBridge Troubleshooting Guide

## Issue: Scale Shows "Connected" But No Weight Values

### Symptoms
- Terminal shows "Scale connected!"
- Web interface (localhost:8080) shows "Scale Connected"
- But weight values never appear / stay blank
- WebSocket returns `weight: None`

### Root Cause
The **PMA Evolution scale** (VID: 0x24BC, PID: 0x2010) internally uses an FTDI-style USB-to-serial chip, even though it has Sartorius vendor/product IDs.

Without proper serial configuration, the scale only sends 2-byte status packets (`\x01\x60`) instead of actual weight data.

### The Fix
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

This was added to `sartorius_web_server.py` in the `connect()` method for ALL scale types.

### How to Diagnose

1. **Check what the scale is sending:**
   ```bash
   pkill -f sartorius_web_server  # Stop server first
   python3 -c "
   import usb.core
   import usb.util
   dev = usb.core.find(idVendor=0x24BC, idProduct=0x2010)
   dev.set_configuration()
   cfg = dev.get_active_configuration()
   intf = cfg[(0, 0)]
   ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
   usb.util.claim_interface(dev, 0)
   for i in range(10):
       try:
           data = dev.read(ep_in.bEndpointAddress, 64, timeout=500)
           print(f'Data: {bytes(data)}')
       except: pass
   "
   ```

2. **If you only see `b'\x01\x60'`** (2-byte status packets), the FTDI configuration is not being applied.

3. **If you see longer packets** with ASCII text, the scale is working correctly.

### Other Common Issues

#### Safari doesn't work
- **Cause:** Safari blocks `ws://localhost` from HTTPS pages (mixed content)
- **Fix:** Use Chrome instead

#### macOS app doesn't open Terminal
- **Cause:** App bundle needs to use `os.system()` not `subprocess.run()` for the `open` command
- **Fix:** Already fixed in current version

#### Windows: "No scale detected"
- **Cause:** libusb driver not installed
- **Fix:** Use Zadig (https://zadig.akeo.ie/) to install WinUSB or libusb-win32 driver for the scale

### Files Overview

| File | Location | Purpose |
|------|----------|---------|
| SartoriusBridge.app | /Applications/ | Menu bar app |
| sartorius_web_server.py | ~/ | WebSocket server (the fix is here) |
| start_sartorius_server.command | ~/ | Launcher script that Terminal opens |

### Contact
If issues persist, check the GitHub repo: https://github.com/briandperla/SartoriusBridge
