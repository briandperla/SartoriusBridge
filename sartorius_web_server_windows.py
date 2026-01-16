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

# Re-export clients from core for tray app
clients = sartorius_core.clients


async def main():
    """Main entry point for the Windows server."""
    await sartorius_core.run_server("Sartorius Bridge - Windows")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
