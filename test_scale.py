#!/usr/bin/env python3
"""
Quick test script to verify scale connection and communication.
Run this to diagnose issues before starting the full server.

Usage: python3 test_scale.py
"""

import sys
import time

# Find and load libusb (same as main server)
import os
import ctypes

libusb_paths = [
    "/opt/homebrew/lib/libusb-1.0.dylib",
    "/opt/homebrew/lib/libusb-1.0.0.dylib",
    "/usr/local/lib/libusb-1.0.dylib",
    "/usr/local/lib/libusb-1.0.0.dylib",
]
for path in libusb_paths:
    if os.path.exists(path):
        try:
            ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
            break
        except OSError:
            continue

import usb.core
import usb.util

# Supported scales
SCALES = [
    (0x24BC, 0x2010, "PMA Evolution"),
    (0x0403, 0x6001, "PMA Power"),
]

def test_scale():
    print("=" * 50)
    print("  SartoriusBridge Scale Test")
    print("=" * 50)
    print()

    # Find scale
    dev = None
    scale_name = None

    for vid, pid, name in SCALES:
        dev = usb.core.find(idVendor=vid, idProduct=pid)
        if dev:
            scale_name = name
            print(f"✓ Found: {name}")
            print(f"  VID: {hex(vid)}, PID: {hex(pid)}")
            print()
            break

    if not dev:
        print("✗ No scale found!")
        print()
        print("  Make sure:")
        print("  - Scale is plugged in via USB")
        print("  - Scale is powered on")
        print("  - No other app is using the scale")
        print()
        print("  Supported scales:")
        for vid, pid, name in SCALES:
            print(f"    - {name} ({hex(vid)}:{hex(pid)})")
        return False

    # Configure FTDI
    print("Configuring serial settings...")
    try:
        dev.ctrl_transfer(0x40, 0x00, 0, 0, None)  # Reset
        dev.ctrl_transfer(0x40, 0x03, 0x4138, 0, None)  # Baud rate: 9600
        dev.ctrl_transfer(0x40, 0x04, 0x0008, 0, None)  # 8N1
        dev.ctrl_transfer(0x40, 0x02, 0, 0, None)  # No flow control
        dev.ctrl_transfer(0x40, 0x01, 0x0303, 0, None)  # DTR/RTS high
        dev.ctrl_transfer(0x40, 0x09, 16, 0, None)  # Latency
        print("✓ Serial settings configured")
    except usb.core.USBError as e:
        print(f"! Serial config failed: {e}")
        print("  (Continuing anyway...)")
    print()

    # Claim interface
    try:
        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]

        ep_in = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        )
        ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )

        usb.util.claim_interface(dev, 0)
        print("✓ Interface claimed")
    except Exception as e:
        print(f"✗ Failed to claim interface: {e}")
        return False

    # Request weight
    print()
    print("Requesting weight data...")
    try:
        dev.write(ep_out.bEndpointAddress, b'\x1bP\r\n', timeout=1000)
        print("✓ Weight request sent")
    except usb.core.USBError as e:
        print(f"✗ Failed to send request: {e}")

    # Read data
    print()
    print("Reading data for 5 seconds...")
    print("-" * 50)

    buffer = b''
    got_weight = False
    start = time.time()

    while time.time() - start < 5:
        try:
            raw = bytes(dev.read(ep_in.bEndpointAddress, 64, timeout=200))

            if raw == b'\x01\x60':
                # Just status bytes, no data
                continue

            if len(raw) > 2:
                buffer += raw[2:]

                if b'\r\n' in buffer:
                    line, buffer = buffer.split(b'\r\n', 1)
                    text = line.decode('ascii', errors='replace').strip()
                    if text:
                        print(f"  WEIGHT: {text}")
                        got_weight = True

        except usb.core.USBTimeoutError:
            pass

    print("-" * 50)
    print()

    # Release
    try:
        usb.util.release_interface(dev, 0)
    except:
        pass

    # Summary
    if got_weight:
        print("✓ SUCCESS! Scale is working correctly.")
        print()
        print("  You can now run the full server:")
        print("  - Open SartoriusBridge from Applications, or")
        print("  - Run: python3 ~/sartorius_web_server.py")
    else:
        print("✗ No weight data received!")
        print()
        print("  The scale is connected but not sending data.")
        print("  Check:")
        print("  - Scale display shows a weight value")
        print("  - Try pressing PRINT button on scale")
        print("  - Check scale menu for USB/Interface settings")

    return got_weight


if __name__ == "__main__":
    try:
        success = test_scale()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
