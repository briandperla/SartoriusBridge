#!/usr/bin/env python3
"""
Sartorius Bridge System Tray App for Windows
Runs the scale WebSocket server with a system tray icon
"""

import threading
import subprocess
import sys
import os
import time

# For Windows system tray
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
except ImportError:
    print("Please install: pip install pystray pillow")
    sys.exit(1)

# Import the Windows server module (uses pyserial, not pyusb)
from sartorius_web_server_windows import main as run_server, scale, clients
import sartorius_core
import asyncio


class SartoriusBridgeWindows:
    def __init__(self):
        self.server_thread = None
        self.server_running = False
        self.icon = None
        self.loop = None

    def create_icon_image(self, color='gray'):
        """Create a simple scale icon"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Color based on status
        if color == 'green':
            fill = (76, 175, 80, 255)
        elif color == 'yellow':
            fill = (255, 193, 7, 255)
        else:
            fill = (158, 158, 158, 255)

        # Draw a simple scale shape
        # Base
        draw.rectangle([16, 48, 48, 56], fill=fill)
        # Pillar
        draw.rectangle([28, 24, 36, 48], fill=fill)
        # Pan
        draw.ellipse([12, 8, 52, 28], fill=fill)

        return image

    def get_status_text(self):
        if not self.server_running:
            return "Status: Not Running"
        elif scale.connected:
            return f"Status: Connected ({len(clients)} clients)"
        else:
            return "Status: Searching for Scale"

    def update_icon(self):
        if not self.server_running:
            self.icon.icon = self.create_icon_image('gray')
        elif scale.connected:
            self.icon.icon = self.create_icon_image('green')
        else:
            self.icon.icon = self.create_icon_image('yellow')

    def start_bridge(self, icon=None, item=None):
        if self.server_running:
            return

        def run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(run_server())
            except Exception as e:
                print(f"Server error: {e}")
            finally:
                self.server_running = False
                if self.icon:
                    self.update_icon()

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        self.server_running = True
        time.sleep(1)  # Give server time to start
        if self.icon:
            self.update_icon()

    def stop_bridge(self, icon=None, item=None):
        if not self.server_running:
            return

        # Signal graceful shutdown
        sartorius_core.request_shutdown()

        self.server_running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

        # Wait for thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2.0)

        # Clear references
        self.loop = None
        self.server_thread = None

        if self.icon:
            self.update_icon()

    def reconnect_scale(self, icon=None, item=None):
        """Manually trigger scale reconnection."""
        if not self.server_running:
            return

        def do_reconnect():
            success = sartorius_core.reconnect_scale()
            if self.icon:
                self.update_icon()

        threading.Thread(target=do_reconnect, daemon=True).start()

    def open_test_page(self, icon=None, item=None):
        import webbrowser
        webbrowser.open('http://localhost:8080')

    def open_formulator(self, icon=None, item=None):
        # Open in Chrome specifically (better WebSocket support)
        subprocess.run(['start', 'chrome', 'https://formulator.focalfinishes.com'], shell=True)

    def quit_app(self, icon=None, item=None):
        self.stop_bridge()
        if self.icon:
            self.icon.stop()

    def run(self):
        # Create menu
        menu = pystray.Menu(
            item(lambda text: self.get_status_text(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            item('Start Bridge', self.start_bridge),
            item('Stop Bridge', self.stop_bridge),
            item('Reconnect Scale', self.reconnect_scale),
            pystray.Menu.SEPARATOR,
            item('Open Test Page', self.open_test_page),
            item('Open Formulator', self.open_formulator),
            pystray.Menu.SEPARATOR,
            item('Quit', self.quit_app)
        )

        # Create system tray icon
        self.icon = pystray.Icon(
            'SartoriusBridge',
            self.create_icon_image('gray'),
            'Sartorius Bridge',
            menu
        )

        # Auto-start server
        self.start_bridge()

        # Run the icon (blocks)
        self.icon.run()


def main():
    app = SartoriusBridgeWindows()
    app.run()


if __name__ == "__main__":
    main()
