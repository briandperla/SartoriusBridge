#!/usr/bin/env python3
"""
Sartorius Scale Base Module
Abstract base class defining the scale communication interface.

This module provides:
- SartoriusScaleBase: Abstract base class that all platform adapters must inherit
- SUPPORTED_SCALES: Shared constant with supported scale VID/PID combinations
- _parse_weight(): Shared weight parsing logic (identical across platforms)
"""

from abc import ABC, abstractmethod
import time
from typing import Optional, Dict, Any

# Supported scale USB identifiers (shared across platforms)
# Both Mac (USB) and Windows (COM) use these VID/PID to identify scales
SUPPORTED_SCALES = [
    (0x24BC, 0x2010, "PMA Evolution"),  # Sartorius native USB
    (0x0403, 0x6001, "PMA Power"),      # FTDI FT232
]


class SartoriusScaleBase(ABC):
    """
    Abstract base class for Sartorius scale communication.

    Platform-specific implementations (Mac USB, Windows COM) must inherit
    from this class and implement all abstract methods.

    Attributes:
        buffer: Byte buffer for accumulating partial reads
        _connected: Internal connection state flag
        scale_name: Human-readable name of connected scale
        last_successful_read: Timestamp of last successful data read
    """

    def __init__(self):
        self.buffer = b''
        self._connected = False
        self.scale_name = None
        self.last_successful_read = 0.0  # Timestamp of last successful data read

    @property
    def connected(self) -> bool:
        """Return current connection state."""
        return self._connected

    @connected.setter
    def connected(self, value: bool):
        """Set connection state."""
        self._connected = value

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to scale.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from scale and release resources."""
        pass

    @abstractmethod
    def read_data(self) -> Optional[Dict[str, Any]]:
        """
        Read and parse weight data from scale.

        Returns:
            dict: Parsed weight data with keys: raw, weight, unit, timestamp
            None: If no data available or error occurred
        """
        pass

    @abstractmethod
    def request_weight(self) -> None:
        """Send weight request command (ESC+P) to scale."""
        pass

    @abstractmethod
    def tare(self) -> None:
        """Send tare command (ESC+T) to scale."""
        pass

    @abstractmethod
    def zero(self) -> None:
        """Send zero command to scale (tries multiple commands)."""
        pass

    def _parse_weight(self, text: str) -> Dict[str, Any]:
        """
        Parse weight string from scale response.

        This method is shared across all platform implementations.
        The scale returns strings like "+  123.4 g" or "  45.67 kg".

        Args:
            text: Raw text from scale

        Returns:
            dict with keys:
                - raw: Original text string
                - weight: Parsed float value (or None if parsing failed)
                - unit: Unit string (default 'g')
                - timestamp: Unix timestamp when parsed
        """
        parts = text.split()
        weight = None
        unit = 'g'

        if parts:
            for i, p in enumerate(parts):
                try:
                    # Remove leading + and spaces from numeric part
                    weight = float(p.replace('+', '').replace(' ', ''))
                    # If there's a next part, assume it's the unit
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

    def update_last_read(self) -> None:
        """Update timestamp when data is successfully read."""
        self.last_successful_read = time.time()

    def seconds_since_last_read(self) -> float:
        """Return seconds since last successful read."""
        if self.last_successful_read == 0.0:
            return float('inf')
        return time.time() - self.last_successful_read
