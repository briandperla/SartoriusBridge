#!/usr/bin/env python3
"""
Quick test script to verify scale connection and communication on Windows.
Uses pyserial to communicate via the Sartorius Virtual COM Port.

Usage: python test_scale_windows.py
"""

import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Please install: pip install pyserial")
    sys.exit(1)

# Supported scales
SCALES = [
    (0x24BC, 0x2010, "PMA Evolution"),
    (0x0403, 0x6001, "PMA Power"),
]


def test_scale():
    print("=" * 50)
    print("  SartoriusBridge Windows Scale Test")
    print("=" * 50)
    print()

    # List all COM ports
    ports = serial.tools.list_ports.comports()
    print(f"Found {len(ports)} COM port(s):")
    for port in ports:
        vid_pid = ""
        if port.vid and port.pid:
            vid_pid = f" [{hex(port.vid)}:{hex(port.pid)}]"
        print(f"  - {port.device}: {port.description}{vid_pid}")
    print()

    # Find scale port
    scale_port = None
    scale_name = None

    for port in ports:
        if port.vid and port.pid:
            for vid, pid, name in SCALES:
                if port.vid == vid and port.pid == pid:
                    scale_port = port.device
                    scale_name = name
                    break
        if scale_port:
            break

        # Fallback: check description
        desc = (port.description or '').lower()
        if 'sartorius' in desc or 'pma' in desc:
            scale_port = port.device
            scale_name = "Sartorius Scale"
            break

    if not scale_port:
        print("X No scale found!")
        print()
        print("  Make sure:")
        print("  - Scale is plugged in via USB")
        print("  - Scale is powered on")
        print("  - Sartorius 'Driver PMA' is installed")
        print()
        print("  Supported scales:")
        for vid, pid, name in SCALES:
            print(f"    - {name} ({hex(vid)}:{hex(pid)})")
        print()
        print("  Install the Sartorius driver from:")
        print("  https://www.sartorius.com (search for 'Driver PMA')")
        return False

    print(f"Found: {scale_name} on {scale_port}")
    print()

    # Connect to scale
    print("Connecting...")
    try:
        ser = serial.Serial(
            port=scale_port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5,
            write_timeout=1.0
        )
        print("Connected!")
    except serial.SerialException as e:
        print(f"X Failed to connect: {e}")
        return False

    # Request weight
    print()
    print("Requesting weight data...")
    try:
        ser.write(b'\x1bP\r\n')
        print("Weight request sent (ESC+P)")
    except serial.SerialException as e:
        print(f"X Failed to send request: {e}")
        ser.close()
        return False

    # Read data
    print()
    print("Reading data for 5 seconds...")
    print("-" * 50)

    buffer = b''
    got_weight = False
    start = time.time()

    while time.time() - start < 5:
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer += data

                if b'\r\n' in buffer:
                    line, buffer = buffer.split(b'\r\n', 1)
                    text = line.decode('ascii', errors='replace').strip()
                    if text:
                        print(f"  WEIGHT: {text}")
                        got_weight = True

            # Request again
            if time.time() - start > 2 and not got_weight:
                ser.write(b'\x1bP\r\n')
                time.sleep(0.5)
        except serial.SerialException:
            pass
        time.sleep(0.1)

    print("-" * 50)
    print()

    # Close
    ser.close()

    # Summary
    if got_weight:
        print("SUCCESS! Scale is working correctly.")
        print()
        print("  You can now run the full server:")
        print("  - Run SartoriusBridge.exe, or")
        print("  - Run: python sartorius_web_server_windows.py")
    else:
        print("X No weight data received!")
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
        input("\nPress Enter to exit...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
