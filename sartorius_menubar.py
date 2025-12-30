#!/usr/bin/env python3
"""
Sartorius Bridge Menu Bar App
Runs the scale WebSocket server silently with a menu bar icon
"""

import rumps
import subprocess
import signal
import os
import sys
import time

class SartoriusBridgeApp(rumps.App):
    def __init__(self):
        super(SartoriusBridgeApp, self).__init__(
            "Sartorius Bridge",
            icon=None,
            title="⚖️"
        )
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

        # Auto-start the server
        self.start_server(None)

    def update_status(self, running, scale_connected=False):
        if running:
            if scale_connected:
                self.title = "⚖️✓"
                self.status_item.title = "Status: Connected"
            else:
                self.title = "⚖️"
                self.status_item.title = "Status: Running (No Scale)"
        else:
            self.title = "⚖️✗"
            self.status_item.title = "Status: Not Running"

    def is_port_in_use(self, port):
        """Check if a port is already in use"""
        result = subprocess.run(f"lsof -ti:{port}", shell=True, capture_output=True, text=True)
        return bool(result.stdout.strip())

    @rumps.clicked("Start Server")
    def start_server(self, _):
        # Check if port 8765 is already in use (server running from another instance)
        if self.is_port_in_use(8765):
            self.update_status(True)
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server already running on port 8765"
            )
            return

        # Find the launcher script
        home = os.path.expanduser("~")
        launcher_script = os.path.join(home, "start_sartorius_server.command")

        if not os.path.exists(launcher_script):
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="Error",
                message=f"Launcher not found at {launcher_script}"
            )
            return

        # Open the .command file - this opens Terminal without needing Automation permission
        os.system(f'open "{launcher_script}"')

        # Wait a moment for server to start, then update status
        time.sleep(2)
        if self.is_port_in_use(8765):
            self.update_status(True)
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server started in Terminal on port 8765"
            )
        else:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server may still be starting..."
            )

    @rumps.clicked("Stop Server")
    def stop_server(self, _):
        if not self.is_port_in_use(8765):
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server is not running"
            )
            return

        # Kill processes on server ports
        subprocess.run("lsof -ti:8765 -ti:8080 | xargs kill 2>/dev/null", shell=True)

        self.update_status(False)
        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Server stopped"
        )

    @rumps.clicked("Open Formulator")
    def open_formulator(self, _):
        subprocess.run(["open", "http://localhost:3000"])

    def cleanup(self):
        # Kill any remaining processes on these ports
        subprocess.run("lsof -ti:8765 -ti:8080 | xargs kill 2>/dev/null", shell=True)

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
