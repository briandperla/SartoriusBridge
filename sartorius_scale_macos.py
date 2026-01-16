#!/usr/bin/env python3
"""
Sartorius Scale macOS Module
USB communication implementation using pyusb/libusb.

This module handles:
- libusb library preloading for macOS
- USB device discovery and connection
- FTDI-style serial protocol over USB
"""

import os
import ctypes
import time
from typing import Optional, Dict, Any

# Fix libusb path for macOS (Homebrew installs)
# This must be done BEFORE importing usb.core
def find_and_load_libusb():
    """Find and preload libusb library for pyusb"""
    # Common Homebrew paths
    libusb_paths = [
        "/opt/homebrew/lib/libusb-1.0.dylib",  # Apple Silicon
        "/opt/homebrew/lib/libusb-1.0.0.dylib",
        "/usr/local/lib/libusb-1.0.dylib",      # Intel Mac
        "/usr/local/lib/libusb-1.0.0.dylib",
    ]
    for path in libusb_paths:
        if os.path.exists(path):
            try:
                # Preload the library so pyusb can find it
                ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
                return path
            except OSError:
                continue
    return None

# Preload libusb before importing usb modules
_libusb_path = find_and_load_libusb()

import usb.core
import usb.util
import usb.backend.libusb1 as libusb1

# Create backend with explicit library path if needed
_backend = None
if _libusb_path:
    try:
        _backend = libusb1.get_backend(find_library=lambda x: _libusb_path)
    except OSError:
        pass

# Import base class after USB setup
from sartorius_scale_base import SartoriusScaleBase, SUPPORTED_SCALES

# Track if libusb warning has been shown
_libusb_warning_shown = False


class SartoriusScaleMacOS(SartoriusScaleBase):
    """
    Sartorius scale communication via USB (macOS).

    Uses pyusb with libusb backend for direct USB communication.
    Supports both PMA Evolution (native USB) and PMA Power (FTDI).
    """

    def __init__(self):
        super().__init__()
        self.dev = None       # USB device object
        self.ep_in = None     # Input endpoint
        self.ep_out = None    # Output endpoint

    def connect(self) -> bool:
        """
        Connect to scale via USB.

        Tries each supported scale VID/PID combination until one is found.
        Configures FTDI-style serial settings for communication.

        Returns:
            bool: True if connection successful
        """
        global _libusb_warning_shown

        # Try each supported scale VID/PID combination
        for vid, pid, name in SUPPORTED_SCALES:
            try:
                if _backend:
                    self.dev = usb.core.find(idVendor=vid, idProduct=pid, backend=_backend)
                else:
                    self.dev = usb.core.find(idVendor=vid, idProduct=pid)
                if self.dev:
                    self.scale_name = name
                    break  # Found a scale
            except usb.core.NoBackendError:
                # libusb not available - common in macOS app bundles (show warning only once)
                if not _libusb_warning_shown:
                    print("Warning: libusb not available. Scale functionality disabled.")
                    print("To enable scale, run from Terminal: python3 ~/sartorius_web_server.py")
                    _libusb_warning_shown = True
                self.dev = None
                break
            except usb.core.USBError as e:
                if not _libusb_warning_shown:
                    print(f"USB error: {e}")
                self.dev = None

        if not self.dev:
            return False

        try:
            # Configure serial settings - both scale types use FTDI-style protocol
            try:
                self.dev.ctrl_transfer(0x40, 0x00, 0, 0, None)  # Reset
                self.dev.ctrl_transfer(0x40, 0x03, 0x4138, 0, None)  # Baud rate: 9600
                self.dev.ctrl_transfer(0x40, 0x04, 0x0008, 0, None)  # Data format: 8N1
                self.dev.ctrl_transfer(0x40, 0x02, 0, 0, None)  # Flow control: none
                self.dev.ctrl_transfer(0x40, 0x01, 0x0303, 0, None)  # DTR/RTS high
                self.dev.ctrl_transfer(0x40, 0x09, 16, 0, None)  # Latency timer
                print(f"Configured serial settings for {self.scale_name}")
            except usb.core.USBError as e:
                print(f"Note: Serial config not supported ({e})")

            self.dev.set_configuration()
            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 0)]

            self.ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )
            self.ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )

            usb.util.claim_interface(self.dev, 0)
            self._connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from scale and release USB interface."""
        if self.dev:
            try:
                usb.util.release_interface(self.dev, 0)
            except (usb.core.USBError, AttributeError):
                pass
            try:
                usb.util.dispose_resources(self.dev)
            except (usb.core.USBError, AttributeError):
                pass
            self.dev = None
            self.ep_in = None
            self.ep_out = None
        self._connected = False
        self.last_successful_read = 0.0  # Reset timestamp

    def request_weight(self) -> None:
        """Send weight request command (ESC+P)."""
        if self._connected:
            try:
                self.dev.write(self.ep_out.bEndpointAddress, b'\x1bP\r\n', timeout=1000)
            except usb.core.USBError:
                # USB error means device is gone (sleep/wake, unplugged)
                self._connected = False

    def tare(self) -> None:
        """Send tare command (ESC+T)."""
        if self._connected:
            try:
                self.dev.write(self.ep_out.bEndpointAddress, b'\x1bT\r\n', timeout=1000)
            except usb.core.USBError:
                self._connected = False

    def zero(self) -> None:
        """Send zero command (tries multiple commands)."""
        if self._connected:
            try:
                # Try different zero commands that Sartorius scales might use
                self.dev.write(self.ep_out.bEndpointAddress, b'\x1bZ\r\n', timeout=1000)  # ESC+Z
                time.sleep(0.1)
                self.dev.write(self.ep_out.bEndpointAddress, b'\x1b0\r\n', timeout=1000)  # ESC+0
                time.sleep(0.1)
                # Some scales use tare when empty as zero
                self.dev.write(self.ep_out.bEndpointAddress, b'\x1bT\r\n', timeout=1000)  # ESC+T (tare)
            except usb.core.USBError:
                self._connected = False

    def read_data(self) -> Optional[Dict[str, Any]]:
        """
        Read and parse weight data from scale.

        USB reads return FTDI status bytes in first 2 bytes, which are stripped.

        Returns:
            dict: Parsed weight data or None if no data available
        """
        if not self._connected:
            return None

        try:
            raw = bytes(self.dev.read(self.ep_in.bEndpointAddress, 64, timeout=100))
            if len(raw) > 2:
                # Strip FTDI status bytes (first 2 bytes)
                self.buffer += raw[2:]

                if b'\r\n' in self.buffer:
                    line, self.buffer = self.buffer.split(b'\r\n', 1)
                    text = line.decode('ascii', errors='replace').strip()
                    if text:
                        self.update_last_read()  # Track successful read
                        return self._parse_weight(text)
        except usb.core.USBError as e:
            # USB error means device is gone (sleep/wake, unplugged)
            # Timeout errors (errno 60) are normal when no data available
            if e.errno != 60:  # Not a timeout
                print(f"USB error - marking disconnected: {e}")
                self._connected = False
        except Exception as e:
            print(f"Unexpected error - marking disconnected: {e}")
            self._connected = False

        return None


# Convenience alias for backward compatibility
SartoriusScale = SartoriusScaleMacOS
