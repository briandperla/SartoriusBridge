#!/usr/bin/env python3
"""
Sartorius Scale Communication Module for Windows
Uses pyserial to communicate via Virtual COM Port

The Sartorius "Driver PMA" creates a standard COM port on Windows,
allowing communication without libusb or Zadig.
"""

import time

import serial
import serial.tools.list_ports

# Supported scale USB identifiers (for COM port detection)
SUPPORTED_SCALES = [
    (0x24BC, 0x2010, "PMA Evolution"),  # Sartorius native USB
    (0x0403, 0x6001, "PMA Power"),      # FTDI FT232
]


class SartoriusScale:
    """Sartorius scale communication via COM port (Windows)."""

    def __init__(self):
        self.serial_port = None
        self.port_name = None
        self.buffer = b''
        self.connected = False
        self.scale_name = None

    def find_scale_port(self):
        """
        Auto-detect the scale's COM port.

        Returns:
            tuple: (port_name, scale_name) or (None, None) if not found
        """
        try:
            ports = serial.tools.list_ports.comports()
        except Exception:
            return None, None

        for port in ports:
            # Check by VID/PID
            if port.vid and port.pid:
                for vid, pid, name in SUPPORTED_SCALES:
                    if port.vid == vid and port.pid == pid:
                        return port.device, name

            # Fallback: check description for known strings
            desc = (port.description or '').lower()
            if 'sartorius' in desc:
                return port.device, "Sartorius Scale"
            if 'pma' in desc:
                return port.device, "PMA Scale"

        return None, None

    def connect(self):
        """
        Connect to the scale via COM port.

        Returns:
            bool: True if connection successful
        """
        port_name, scale_name = self.find_scale_port()

        if not port_name:
            return False

        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,  # Non-blocking read
                write_timeout=1.0
            )
            self.port_name = port_name
            self.scale_name = scale_name
            self.connected = True
            print(f"Scale connected: {scale_name} on {port_name}")
            return True
        except serial.SerialException as e:
            print(f"Connection error: {e}")
            return False

    def request_weight(self):
        """Send weight request command (ESC+P)."""
        if self.connected and self.serial_port:
            try:
                self.serial_port.write(b'\x1bP\r\n')
            except serial.SerialException:
                self.connected = False

    def tare(self):
        """Send tare command (ESC+T)."""
        if self.connected and self.serial_port:
            try:
                self.serial_port.write(b'\x1bT\r\n')
            except serial.SerialException:
                pass

    def zero(self):
        """Send zero command (multiple attempts)."""
        if self.connected and self.serial_port:
            try:
                self.serial_port.write(b'\x1bZ\r\n')  # ESC+Z
                time.sleep(0.1)
                self.serial_port.write(b'\x1b0\r\n')  # ESC+0
                time.sleep(0.1)
                self.serial_port.write(b'\x1bT\r\n')  # ESC+T (tare)
            except serial.SerialException:
                pass

    def read_data(self):
        """
        Read and parse weight data from scale.

        Returns:
            dict: Parsed weight data or None
        """
        if not self.connected or not self.serial_port:
            return None

        try:
            # Check if data is available
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.read(self.serial_port.in_waiting)
                if data:
                    # pyserial returns raw data (no FTDI status bytes to strip)
                    self.buffer += data

                    if b'\r\n' in self.buffer:
                        line, self.buffer = self.buffer.split(b'\r\n', 1)
                        text = line.decode('ascii', errors='replace').strip()
                        if text:
                            return self._parse_weight(text)
        except serial.SerialException:
            self.connected = False

        return None

    def _parse_weight(self, text):
        """
        Parse weight string from scale response.

        Args:
            text: Raw text from scale

        Returns:
            dict: Parsed weight data
        """
        parts = text.split()
        weight = None
        unit = 'g'

        for i, p in enumerate(parts):
            try:
                weight = float(p.replace('+', '').replace(' ', ''))
                if i + 1 < len(parts):
                    unit = parts[i + 1]
                break
            except ValueError:
                continue

        return {
            'raw': text,
            'weight': weight,
            'unit': unit,
            'timestamp': time.time()
        }

    def disconnect(self):
        """Close the serial connection."""
        if self.serial_port:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.connected = False
        self.serial_port = None
        self.port_name = None
