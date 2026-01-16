#!/usr/bin/env python3
"""
Sartorius PMA Scale - macOS WebSocket Server

This creates a local WebSocket server that bridges the scale to web browsers.
Chrome (or any browser) can connect to ws://localhost:8765 to receive weight data.

USAGE:
    python3 sartorius_web_server.py

Then open http://localhost:8080 in Chrome to see the scale interface.

Press Ctrl+C to stop the server.
"""

import asyncio

# Import shared core module
import sartorius_core

# Import Mac-specific scale class
from sartorius_scale_macos import SartoriusScaleMacOS


# Create scale instance and register with core
scale = SartoriusScaleMacOS()
sartorius_core.scale = scale

# Export clients for state monitoring (used by menubar app)
clients = sartorius_core.clients


async def main():
    """Entry point for in-process server (used by menubar app)."""
    await sartorius_core.run_server("Sartorius PMA Evolution - macOS")


if __name__ == "__main__":
    try:
        asyncio.run(sartorius_core.run_server("Sartorius PMA Evolution - macOS"))
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
