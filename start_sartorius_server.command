#!/bin/bash
# SartoriusBridge Server Launcher
# This script is called by the menu bar app to start the WebSocket server

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the server
cd "$DIR"
python3 sartorius_web_server.py
