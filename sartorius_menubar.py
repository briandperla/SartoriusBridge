#!/usr/bin/env python3
"""
Sartorius Bridge Menu Bar App
Runs the scale WebSocket server in-process with a menu bar icon.

The server runs in a background thread using asyncio, matching the
Windows implementation pattern for reliable Stop/Start functionality.
"""

import rumps
import subprocess
import signal
import os
import sys
import time
import asyncio
import threading

# Import server entry point and shared state
from sartorius_web_server import main as run_server, scale, clients
import sartorius_core


class SartoriusBridgeApp(rumps.App):
    def __init__(self):
        # Get the directory where this script/app is located
        if getattr(sys, 'frozen', False):
            self.app_dir = sys._MEIPASS
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))

        super(SartoriusBridgeApp, self).__init__(
            "Sartorius Bridge",
            icon=os.path.join(self.app_dir, "menubar_gray.png"),
            title=None
        )

        # Server thread management
        self.server_thread = None
        self.server_running = False
        self.loop = None

        self.menu = [
            rumps.MenuItem("Status: Not Running", callback=None),
            None,  # Separator
            rumps.MenuItem("Start Server", callback=self.start_server),
            rumps.MenuItem("Stop Server", callback=self.stop_server),
            None,  # Separator
            rumps.MenuItem("Open Formulator", callback=self.open_formulator),
            None,  # Separator
        ]
        self.status_item = self.menu["Status: Not Running"]

        # Show startup notification
        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Starting scale server..."
        )

        # Auto-start the server
        self.start_server(None)

    def update_status(self):
        """Update menu bar icon and status text based on actual server state."""
        if not self.server_running:
            self.icon = os.path.join(self.app_dir, "menubar_gray.png")
            self.status_item.title = "Status: Not Running"
        elif scale and scale.connected:
            self.icon = os.path.join(self.app_dir, "menubar_green.png")
            self.status_item.title = f"Status: Connected ({len(clients)} clients)"
        else:
            self.icon = os.path.join(self.app_dir, "menubar_yellow.png")
            self.status_item.title = "Status: Running (No Scale)"

    @rumps.clicked("Start Server")
    def start_server(self, _):
        """Start the WebSocket server in a background thread."""
        if self.server_running:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server already running"
            )
            return

        def run():
            """Thread target: create event loop and run server."""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(run_server())
            except Exception as e:
                print(f"Server error: {e}")
            finally:
                self.server_running = False
                # Schedule UI update on next tick
                rumps.Timer(lambda _: self.update_status(), 0.1).start()

        # Start server in daemon thread (won't block app shutdown)
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        self.server_running = True

        # Give server time to start, then update UI
        time.sleep(1)
        self.update_status()

        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Server started"
        )

    @rumps.clicked("Stop Server")
    def stop_server(self, _):
        """Stop the WebSocket server cleanly."""
        if not self.server_running:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server is not running"
            )
            return

        # Signal graceful shutdown (disconnects scale, stops loops)
        sartorius_core.request_shutdown()

        self.server_running = False
        if self.loop:
            # Thread-safe way to stop the event loop
            self.loop.call_soon_threadsafe(self.loop.stop)

        # Wait for server thread to finish (with timeout)
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2.0)

        # Clear references
        self.loop = None
        self.server_thread = None

        self.update_status()

        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Server stopped"
        )

    @rumps.clicked("Open Formulator")
    def open_formulator(self, _):
        subprocess.run(["open", "https://formulator.focalfinishes.com"])

    def cleanup(self):
        """Clean shutdown of server."""
        if self.server_running:
            sartorius_core.request_shutdown()
            self.server_running = False
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2.0)


def main():
    app = SartoriusBridgeApp()

    # Handle cleanup on quit
    def signal_handler(sig, frame):
        app.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app.run()


if __name__ == "__main__":
    main()
