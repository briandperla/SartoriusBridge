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
            return "Server: Stopped"
        elif scale.connected:
            return f"Scale: Connected ({len(clients)} clients)"
        else:
            return "Server: Running (No Scale)"

    def update_icon(self):
        if not self.server_running:
            self.icon.icon = self.create_icon_image('gray')
        elif scale.connected:
            self.icon.icon = self.create_icon_image('green')
        else:
            self.icon.icon = self.create_icon_image('yellow')

    def start_server(self, icon=None, item=None):
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

    def stop_server(self, icon=None, item=None):
        if not self.server_running:
            return

        self.server_running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.icon:
            self.update_icon()

    def open_test_page(self, icon=None, item=None):
        import webbrowser
        webbrowser.open('http://localhost:8080')

    def open_formulator(self, icon=None, item=None):
        import webbrowser
        webbrowser.open('https://formulator.focalfinishes.com')

    def quit_app(self, icon=None, item=None):
        self.stop_server()
        if self.icon:
            self.icon.stop()

    def run(self):
        # Create menu
        menu = pystray.Menu(
            item(lambda text: self.get_status_text(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            item('Start Server', self.start_server),
            item('Stop Server', self.stop_server),
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
        self.start_server()

        # Run the icon (blocks)
        self.icon.run()


def main():
    app = SartoriusBridgeWindows()
    app.run()


if __name__ == "__main__":
    main()
