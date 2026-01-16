#!/usr/bin/env python3
"""
Sartorius Bridge - Windows WebSocket Server

This creates a local WebSocket server that bridges the scale to web browsers.
Chrome (or any browser) can connect to ws://localhost:8765 to receive weight data.

Windows version uses pyserial to communicate via the Sartorius Virtual COM Port.
"""

import asyncio

# Import the Windows scale module (uses pyserial)
from sartorius_scale_windows import SartoriusScaleWindows

# Import shared core module
import sartorius_core

# Create scale instance and register with core
scale = SartoriusScaleWindows()
sartorius_core.scale = scale


if __name__ == "__main__":
    try:
        asyncio.run(sartorius_core.run_server("Sartorius Bridge - Windows"))
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
