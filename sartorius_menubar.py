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
import threading
import asyncio
import json
import http.server
import socketserver
import ctypes

# Fix libusb path for macOS (Homebrew installs)
def find_and_load_libusb():
    """Find and preload libusb library for pyusb"""
    # Check if running as bundled app
    if getattr(sys, 'frozen', False):
        # Look for libusb in the app bundle first
        bundle_path = os.path.join(sys._MEIPASS, 'libusb-1.0.dylib')
        if os.path.exists(bundle_path):
            try:
                ctypes.CDLL(bundle_path, mode=ctypes.RTLD_GLOBAL)
                return bundle_path
            except OSError:
                pass

    # Common Homebrew paths
    libusb_paths = [
        "/opt/homebrew/lib/libusb-1.0.dylib",  # Apple Silicon
        "/opt/homebrew/lib/libusb-1.0.0.dylib",
        "/usr/local/lib/libusb-1.0.dylib",      # Intel Mac
        "/usr/local/lib/libusb-1.0.0.dylib",
    ]
    for path in libusb_paths:
        if os.path.exists(path):
            try:
                ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
                return path
            except OSError:
                continue
    return None

# Preload libusb before importing usb modules
_libusb_path = find_and_load_libusb()

try:
    import usb.core
    import usb.util
    import usb.backend.libusb1 as libusb1
    USB_AVAILABLE = True

    # Create backend with explicit library path if needed
    _backend = None
    if _libusb_path:
        try:
            _backend = libusb1.get_backend(find_library=lambda x: _libusb_path)
        except OSError:
            pass
except ImportError:
    USB_AVAILABLE = False
    _backend = None

try:
    import websockets
    from websockets.asyncio.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    try:
        import websockets
        from websockets.server import serve
        WEBSOCKETS_AVAILABLE = True
    except ImportError:
        WEBSOCKETS_AVAILABLE = False

# Configuration
WEBSOCKET_PORT = 8765
HTTP_PORT = 8080

# Supported scale USB identifiers
SUPPORTED_SCALES = [
    (0x24BC, 0x2010, "PMA Evolution"),
    (0x0403, 0x6001, "PMA Power"),
]


class SartoriusScale:
    """USB scale communication class"""
    def __init__(self):
        self.dev = None
        self.ep_in = None
        self.ep_out = None
        self.buffer = b''
        self.connected = False
        self.scale_name = None

    def connect(self):
        if not USB_AVAILABLE:
            return False

        for vid, pid, name in SUPPORTED_SCALES:
            try:
                if _backend:
                    self.dev = usb.core.find(idVendor=vid, idProduct=pid, backend=_backend)
                else:
                    self.dev = usb.core.find(idVendor=vid, idProduct=pid)
                if self.dev:
                    self.scale_name = name
                    break
            except Exception:
                self.dev = None

        if not self.dev:
            return False

        try:
            try:
                self.dev.ctrl_transfer(0x40, 0x00, 0, 0, None)
                self.dev.ctrl_transfer(0x40, 0x03, 0x4138, 0, None)
                self.dev.ctrl_transfer(0x40, 0x04, 0x0008, 0, None)
                self.dev.ctrl_transfer(0x40, 0x02, 0, 0, None)
                self.dev.ctrl_transfer(0x40, 0x01, 0x0303, 0, None)
                self.dev.ctrl_transfer(0x40, 0x09, 16, 0, None)
            except Exception:
                pass

            self.dev.set_configuration()
            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 0)]

            self.ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )
            self.ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )

            usb.util.claim_interface(self.dev, 0)
            self.connected = True
            return True
        except Exception:
            return False

    def request_weight(self):
        if self.connected:
            try:
                self.dev.write(self.ep_out.bEndpointAddress, b'\x1bP\r\n', timeout=1000)
            except Exception:
                pass

    def tare(self):
        if self.connected:
            try:
                self.dev.write(self.ep_out.bEndpointAddress, b'\x1bT\r\n', timeout=1000)
            except Exception:
                pass

    def read_data(self):
        if not self.connected:
            return None

        try:
            raw = bytes(self.dev.read(self.ep_in.bEndpointAddress, 64, timeout=100))
            if len(raw) > 2:
                self.buffer += raw[2:]

                if b'\r\n' in self.buffer:
                    line, self.buffer = self.buffer.split(b'\r\n', 1)
                    text = line.decode('ascii', errors='replace').strip()
                    if text:
                        return self._parse_weight(text)
        except Exception:
            pass

        return None

    def _parse_weight(self, text):
        parts = text.split()
        weight = None
        unit = 'g'

        if parts:
            for i, p in enumerate(parts):
                try:
                    weight = float(p.replace('+', '').replace(' ', ''))
                    if i + 1 < len(parts):
                        unit = parts[i + 1]
                    break
                except ValueError:
                    continue

        return {'raw': text, 'weight': weight, 'unit': unit, 'timestamp': time.time()}

    def disconnect(self):
        try:
            if self.dev:
                usb.util.release_interface(self.dev, 0)
        except Exception:
            pass
        self.connected = False


class ScaleServer:
    """WebSocket server that bridges scale to web browsers"""
    def __init__(self, status_callback=None):
        self.scale = SartoriusScale()
        self.clients = set()
        self.current_weight = None
        self.running = False
        self.loop = None
        self.status_callback = status_callback
        self._scale_connected = False

    @property
    def scale_connected(self):
        return self._scale_connected

    async def broadcast(self, message):
        if self.clients:
            data = json.dumps(message)
            await asyncio.gather(*[client.send(data) for client in self.clients], return_exceptions=True)

    async def handle_client(self, websocket):
        self.clients.add(websocket)
        await websocket.send(json.dumps({
            'type': 'status',
            'connected': self.scale.connected,
            'weight': self.current_weight
        }))

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    cmd = data.get('command')
                    if cmd == 'tare':
                        self.scale.tare()
                        await websocket.send(json.dumps({'type': 'ack', 'command': 'tare'}))
                    elif cmd == 'read':
                        self.scale.request_weight()
                        await websocket.send(json.dumps({'type': 'ack', 'command': 'read'}))
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        finally:
            self.clients.discard(websocket)

    async def scale_reader(self):
        last_request_time = 0
        REQUEST_INTERVAL = 0.3

        while self.running:
            if not self.scale.connected:
                if self.scale.connect():
                    self._scale_connected = True
                    if self.status_callback:
                        self.status_callback(True, True)
                    await self.broadcast({'type': 'status', 'connected': True})
                    self.scale.request_weight()
                else:
                    if self._scale_connected:
                        self._scale_connected = False
                        if self.status_callback:
                            self.status_callback(True, False)
                        await self.broadcast({'type': 'status', 'connected': False})
                    await asyncio.sleep(2)
                    continue

            current_time = time.time()
            if current_time - last_request_time >= REQUEST_INTERVAL:
                self.scale.request_weight()
                last_request_time = current_time

            result = self.scale.read_data()
            if result:
                self.current_weight = result
                await self.broadcast({'type': 'weight', 'data': result})

            await asyncio.sleep(0.02)

    async def run_server(self):
        self.running = True
        async with serve(self.handle_client, "localhost", WEBSOCKET_PORT):
            await self.scale_reader()

    def start(self):
        def run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.run_server())
            except Exception:
                pass
            finally:
                self.loop.close()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.scale.disconnect()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)


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
        self.menu = [
            rumps.MenuItem("Status: Not Running", callback=None),
            None,
            rumps.MenuItem("Start Server", callback=self.start_server),
            rumps.MenuItem("Stop Server", callback=self.stop_server),
            None,
            rumps.MenuItem("Open Formulator", callback=self.open_formulator),
            None,
        ]
        self.status_item = self.menu["Status: Not Running"]
        self.server = None

        # Show startup notification
        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Starting scale server..."
        )

        # Auto-start the server
        self.start_server(None)

    def update_status(self, running, scale_connected=False):
        """Update menu bar icon and status text"""
        if running:
            if scale_connected:
                self.icon = os.path.join(self.app_dir, "menubar_green.png")
                self.status_item.title = "Status: Scale Connected"
            else:
                self.icon = os.path.join(self.app_dir, "menubar_yellow.png")
                self.status_item.title = "Status: Waiting for Scale"
        else:
            self.icon = os.path.join(self.app_dir, "menubar_gray.png")
            self.status_item.title = "Status: Not Running"

    def is_port_in_use(self, port):
        """Check if a port is already in use"""
        result = subprocess.run(f"lsof -ti:{port}", shell=True, capture_output=True, text=True)
        return bool(result.stdout.strip())

    @rumps.clicked("Start Server")
    def start_server(self, _):
        if self.server and self.server.running:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server is already running"
            )
            return

        if self.is_port_in_use(WEBSOCKET_PORT):
            self.update_status(True, False)
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message=f"Port {WEBSOCKET_PORT} already in use"
            )
            return

        if not WEBSOCKETS_AVAILABLE:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="Error",
                message="websockets module not available"
            )
            return

        # Create and start server with status callback
        self.server = ScaleServer(status_callback=self.update_status)
        self.server.start()

        self.update_status(True, False)
        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Server started on port 8765"
        )

    @rumps.clicked("Stop Server")
    def stop_server(self, _):
        if not self.server or not self.server.running:
            rumps.notification(
                title="Sartorius Bridge",
                subtitle="",
                message="Server is not running"
            )
            return

        self.server.stop()
        self.server = None
        self.update_status(False)
        rumps.notification(
            title="Sartorius Bridge",
            subtitle="",
            message="Server stopped"
        )

    @rumps.clicked("Open Formulator")
    def open_formulator(self, _):
        subprocess.run(["open", "https://formulator.focalfinishes.com"])

    def cleanup(self):
        if self.server:
            self.server.stop()


def main():
    app = SartoriusBridgeApp()

    def signal_handler(sig, frame):
        app.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app.run()


if __name__ == "__main__":
    main()
