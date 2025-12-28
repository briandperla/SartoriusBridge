#!/usr/bin/env python3
"""
Sartorius Bridge Menu Bar App
Runs the scale WebSocket server silently with a menu bar icon
"""

import rumps
import threading
import subprocess
import signal
import os
import sys

class SartoriusBridgeApp(rumps.App):
    def __init__(self):
        super(SartoriusBridgeApp, self).__init__(
            "Sartorius Bridge",
            icon=None,
            title="⚖️"
        )
        self.server_process = None
        self.log_handle = None
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
        if self.server_process is not None:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server is already running"
            )
            return

        # Check if port 8765 is already in use (server running from another instance)
        if self.is_port_in_use(8765):
            self.update_status(True)
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server already running on port 8765"
            )
            return

        # Find the server script
        home = os.path.expanduser("~")
        server_script = os.path.join(home, "sartorius_web_server.py")

        if not os.path.exists(server_script):
            # Try in the app bundle
            bundle_script = os.path.join(os.path.dirname(__file__), "sartorius_web_server.py")
            if os.path.exists(bundle_script):
                server_script = bundle_script
            else:
                rumps.notification(
                    title="Sartorius Bridge",
                    subtitle="Error",
                    message="Server script not found!"
                )
                return

        # Start the server in background (discard output to prevent pipe buffer blocking)
        log_file = os.path.join(home, ".sartorius_server.log")
        self.log_handle = open(log_file, 'w')

        # Launch via login shell to get proper library paths (bypasses macOS DYLD stripping)
        shell_cmd = f'export DYLD_LIBRARY_PATH="/opt/homebrew/lib:/usr/local/lib:$DYLD_LIBRARY_PATH"; exec python3 "{server_script}"'
        self.server_process = subprocess.Popen(
            ['/bin/bash', '-l', '-c', shell_cmd],
            stdout=self.log_handle,
            stderr=self.log_handle,
            cwd=home
        )

        self.update_status(True)
        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Server started on port 8765"
        )

    @rumps.clicked("Stop Server")
    def stop_server(self, _):
        if self.server_process is None:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server is not running"
            )
            return

        self.server_process.terminate()
        try:
            self.server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.server_process.kill()
            self.server_process.wait()
        self.server_process = None

        # Close log file handle
        if self.log_handle:
            try:
                self.log_handle.close()
            except OSError:
                pass
            self.log_handle = None

        # Also kill any orphaned processes
        subprocess.run("lsof -ti:8765 -ti:8080 | xargs kill -9 2>/dev/null", shell=True)

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
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
        if self.log_handle:
            try:
                self.log_handle.close()
            except OSError:
                pass
        # Kill any remaining processes on these ports
        subprocess.run("lsof -ti:8765 -ti:8080 | xargs kill -9 2>/dev/null", shell=True)

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
