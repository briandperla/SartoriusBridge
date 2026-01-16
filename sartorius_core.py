#!/usr/bin/env python3
"""
Sartorius Bridge Core Module
Shared server logic for Mac and Windows platforms.

This module contains all common functionality:
- WebSocket server for real-time weight data
- HTTP server for web interface
- Client handling and broadcast logic
- HTML page for the web UI

Platform-specific code (USB vs COM communication) is in separate modules.
"""

import asyncio
import json
import threading
import time
import http.server
import socketserver

import websockets
try:
    from websockets.asyncio.server import serve
except ImportError:
    from websockets.server import serve  # Fallback for older versions

# Configuration
WEBSOCKET_PORT = 8765
HTTP_PORT = 8080

# Global state (will be set by platform-specific code)
scale = None  # Platform-specific scale instance
scale_connected = False
current_weight = None
clients = set()
_shutdown_flag = False  # Signal to stop the server gracefully
_http_server = None  # Reference to HTTP server for shutdown
_failed_connect_attempts = 0  # Track consecutive connection failures
_on_recovery_callback = None  # Callback for UI notification on auto-recovery


def set_recovery_callback(callback):
    """Set callback function to be called when auto-recovery succeeds."""
    global _on_recovery_callback
    _on_recovery_callback = callback


def request_shutdown():
    """Signal the server to shut down gracefully."""
    global _shutdown_flag
    _shutdown_flag = True
    # Disconnect scale
    if scale:
        scale.disconnect()
    # Close all WebSocket clients
    clients.clear()
    # Shutdown HTTP server
    if _http_server:
        _http_server.shutdown()


def reset_shutdown():
    """Reset shutdown flag for restart."""
    global _shutdown_flag, scale_connected, current_weight, _failed_connect_attempts
    _shutdown_flag = False
    scale_connected = False
    current_weight = None
    _failed_connect_attempts = 0


def reconnect_scale() -> bool:
    """
    Manually trigger scale reconnection with USB reset.

    This is called from the UI "Reconnect Scale" menu option.
    It forces a USB reset and reconnection attempt.

    Returns:
        bool: True if reconnection succeeded
    """
    global scale_connected

    if not scale:
        return False

    print("Manual reconnect requested...")

    # Disconnect first
    scale.disconnect()
    scale_connected = False

    # Try USB reset if available (Mac)
    if hasattr(scale, 'reset_usb_device'):
        print("Performing USB reset...")
        scale.reset_usb_device()

    # Try to connect
    if scale.connect():
        scale_connected = True
        scale.update_last_read()
        print("Scale reconnected successfully!")
        return True

    print("Reconnection failed")
    return False


async def broadcast(message):
    """Send message to all connected WebSocket clients."""
    if clients:
        data = json.dumps(message)
        await asyncio.gather(*[client.send(data) for client in clients])


async def handle_client(websocket):
    """Handle a WebSocket client connection."""
    clients.add(websocket)
    print(f"Client connected. Total clients: {len(clients)}")

    # Send current state
    await websocket.send(json.dumps({
        'type': 'status',
        'connected': scale.connected if scale else False,
        'weight': current_weight
    }))

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                cmd = data.get('command')

                if cmd == 'tare':
                    if scale:
                        scale.tare()
                    await websocket.send(json.dumps({'type': 'ack', 'command': 'tare'}))
                elif cmd == 'zero':
                    if scale:
                        scale.zero()
                    await websocket.send(json.dumps({'type': 'ack', 'command': 'zero'}))
                elif cmd == 'read':
                    if scale:
                        scale.request_weight()
                    await websocket.send(json.dumps({'type': 'ack', 'command': 'read'}))
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(clients)}")


async def scale_reader():
    """Background task to read from scale and broadcast updates."""
    global current_weight, scale_connected

    last_request_time = 0
    REQUEST_INTERVAL = 0.3  # Request weight every 300ms for real-time updates
    HEARTBEAT_TIMEOUT = 2.0  # Seconds without data = disconnected

    while not _shutdown_flag:
        # Check heartbeat timeout (no data for 2 seconds = disconnected)
        if scale and scale.connected:
            if scale.seconds_since_last_read() > HEARTBEAT_TIMEOUT:
                print(f"Heartbeat timeout - no data for {HEARTBEAT_TIMEOUT}s")
                scale.disconnect()  # Clean disconnect
                scale_connected = False
                await broadcast({'type': 'status', 'connected': False})

        # Attempt connection if not connected
        if not scale or not scale.connected:
            global _failed_connect_attempts

            if scale:
                scale.disconnect()  # Ensure clean state before reconnect

            connected = False
            if scale:
                connected = scale.connect()

            # If normal connect failed and we have USB reset capability, try it
            if not connected and scale and hasattr(scale, 'reset_usb_device'):
                _failed_connect_attempts += 1

                # After 2 failed attempts, try USB reset (zombie recovery)
                if _failed_connect_attempts >= 2:
                    print(f"Connection failed {_failed_connect_attempts} times, attempting USB reset...")
                    if scale.reset_usb_device():
                        print("USB reset successful, trying to connect...")
                        connected = scale.connect()
                        if connected and _on_recovery_callback:
                            # Notify UI of auto-recovery
                            _on_recovery_callback("Scale connection recovered")
                    _failed_connect_attempts = 0  # Reset counter after trying USB reset

            if connected:
                scale_connected = True
                scale.update_last_read()  # Initialize heartbeat timer
                _failed_connect_attempts = 0  # Reset on successful connection
                print("Scale connected!")
                await broadcast({'type': 'status', 'connected': True})
                scale.request_weight()
            else:
                if scale_connected:
                    scale_connected = False
                    await broadcast({'type': 'status', 'connected': False})
                await asyncio.sleep(2)
                continue

        # Continuously request weight for real-time updates
        current_time = time.time()
        if current_time - last_request_time >= REQUEST_INTERVAL:
            scale.request_weight()
            last_request_time = current_time

        # Read weight data
        result = scale.read_data()
        if result:
            current_weight = result
            await broadcast({
                'type': 'weight',
                'data': result
            })

        await asyncio.sleep(0.02)

    # Cleanup on exit
    print("Scale reader shutting down...")
    if scale:
        scale.disconnect()


# HTML page for the web interface
HTML_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sartorius Bridge</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        .container {
            text-align: center;
            padding: 40px;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 10px;
            opacity: 0.8;
        }
        .status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-bottom: 30px;
        }
        .status.connected { background: rgba(76, 175, 80, 0.3); }
        .status.disconnected { background: rgba(244, 67, 54, 0.3); }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .status.connected .status-dot { background: #4CAF50; }
        .status.disconnected .status-dot { background: #f44336; }
        .weight-display {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px 60px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .weight-value {
            font-size: 5rem;
            font-weight: 300;
            font-variant-numeric: tabular-nums;
            line-height: 1;
        }
        .weight-unit {
            font-size: 2rem;
            opacity: 0.7;
            margin-left: 10px;
        }
        .weight-raw {
            font-size: 0.9rem;
            opacity: 0.5;
            margin-top: 15px;
            font-family: monospace;
        }
        .buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        button {
            padding: 12px 30px;
            font-size: 1rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.2s;
            font-weight: 500;
        }
        button:hover { transform: scale(1.05); }
        button:active { transform: scale(0.98); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-tare { background: #2196F3; color: white; }
        .btn-save { background: #4CAF50; color: white; }
        .btn-clear {
            background: transparent;
            color: rgba(255,255,255,0.5);
            border: 1px solid rgba(255,255,255,0.2);
            margin-top: 10px;
            padding: 8px 20px;
            font-size: 0.85rem;
        }
        .btn-clear:hover { background: rgba(255,255,255,0.1); }
        .history-empty {
            opacity: 0.4;
            font-style: italic;
            padding: 15px;
            text-align: center;
        }
        .history {
            margin-top: 40px;
            text-align: left;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
        }
        .history h3 {
            font-size: 0.9rem;
            opacity: 0.6;
            margin-bottom: 10px;
        }
        .history-list {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 10px;
            max-height: 150px;
            overflow-y: auto;
        }
        .history-item {
            padding: 8px 12px;
            font-family: monospace;
            font-size: 0.9rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .history-item:last-child { border-bottom: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sartorius Bridge</h1>
        <div id="status" class="status disconnected">
            <span class="status-dot"></span>
            <span id="status-text">Connecting...</span>
        </div>

        <div class="weight-display">
            <span id="weight-value" class="weight-value">---</span>
            <span id="weight-unit" class="weight-unit">g</span>
            <div id="weight-raw" class="weight-raw"></div>
        </div>

        <div class="buttons">
            <button class="btn-tare" onclick="sendCommand('tare')">Tare</button>
            <button class="btn-save" onclick="saveReading()">Save Reading</button>
        </div>
        <div style="margin-top: 15px; font-size: 0.8rem; opacity: 0.6;">
            ● Live updating
        </div>

        <div class="history">
            <h3>Saved Readings</h3>
            <div id="history-list" class="history-list">
                <div class="history-empty">Click "Save Reading" to capture weights</div>
            </div>
            <button class="btn-clear" onclick="clearReadings()">Clear All</button>
        </div>
    </div>

    <script>
        let ws;
        let savedReadings = [];
        let currentWeight = null;

        function connect() {
            ws = new WebSocket('ws://localhost:8765');

            ws.onopen = () => {
                console.log('WebSocket connected');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'status') {
                    updateStatus(data.connected);
                    if (data.weight) {
                        updateWeight(data.weight);
                    }
                } else if (data.type === 'weight') {
                    updateWeight(data.data);
                    currentWeight = data.data;
                }
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                updateStatus(false);
                setTimeout(connect, 2000);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        function updateStatus(connected) {
            const el = document.getElementById('status');
            const text = document.getElementById('status-text');

            if (connected) {
                el.className = 'status connected';
                text.textContent = 'Scale Connected';
            } else {
                el.className = 'status disconnected';
                text.textContent = 'Scale Disconnected';
            }
        }

        function updateWeight(data) {
            const valueEl = document.getElementById('weight-value');
            const unitEl = document.getElementById('weight-unit');
            const rawEl = document.getElementById('weight-raw');

            if (data.weight !== null) {
                valueEl.textContent = data.weight.toFixed(1);
            } else {
                valueEl.textContent = '---';
            }

            unitEl.textContent = data.unit || 'g';
            rawEl.textContent = data.raw || '';
        }

        function saveReading() {
            if (!currentWeight || currentWeight.weight === null) {
                return;
            }

            const time = new Date().toLocaleTimeString();
            savedReadings.unshift({
                time,
                weight: currentWeight.weight,
                unit: currentWeight.unit,
                raw: currentWeight.raw
            });

            renderSavedReadings();
        }

        function clearReadings() {
            savedReadings = [];
            renderSavedReadings();
        }

        function renderSavedReadings() {
            const list = document.getElementById('history-list');

            if (savedReadings.length === 0) {
                list.innerHTML = '<div class="history-empty">Click "Save Reading" to capture weights</div>';
            } else {
                list.innerHTML = savedReadings.map((r, i) =>
                    `<div class="history-item">#${savedReadings.length - i}  ${r.time}: <strong>${r.weight} ${r.unit}</strong></div>`
                ).join('');
            }
        }

        function sendCommand(cmd) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ command: cmd }));
            }
        }

        // Start connection
        connect();
    </script>
</body>
</html>
'''


class SimpleHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


class ReusableTCPServer(socketserver.TCPServer):
    """TCP Server that allows address reuse for quick restart."""
    allow_reuse_address = True


def run_http_server():
    global _http_server
    _http_server = ReusableTCPServer(("", HTTP_PORT), SimpleHTTPHandler)
    try:
        _http_server.serve_forever()
    finally:
        _http_server.server_close()
        _http_server = None


async def run_server(app_name="Sartorius Bridge"):
    """Main server entry point."""
    # Reset shutdown state for fresh start
    reset_shutdown()

    print("=" * 55)
    print(f"{app_name} - Web Server")
    print("=" * 55)
    print()
    print(f"  Web Interface:  http://localhost:{HTTP_PORT}")
    print(f"  WebSocket:      ws://localhost:{WEBSOCKET_PORT}")
    print()
    print("Open Chrome and go to the Web Interface URL above.")
    print("Press Ctrl+C to stop the server.")
    print()
    print("-" * 55)

    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    print(f"HTTP server started on port {HTTP_PORT}")

    # Start WebSocket server with reuse_address for quick restart
    try:
        async with serve(handle_client, "localhost", WEBSOCKET_PORT, reuse_address=True):
            print(f"WebSocket server started on port {WEBSOCKET_PORT}")
            print()

            # Run scale reader
            await scale_reader()
    finally:
        print("Server shutdown complete")


if __name__ == "__main__":
    print("This module is meant to be imported, not run directly.")
    print("Use sartorius_web_server.py (Mac) or sartorius_web_server_windows.py (Windows)")
