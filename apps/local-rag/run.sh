#!/bin/bash

# Configuration
DATA_DIR="./data"
PID_FILE="$DATA_DIR/app.pid"
PORT_FILE="$DATA_DIR/app.port"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Function to cleanup files
cleanup_and_exit() {
    local exit_code=${1:-0}
    echo "Cleaning up..."
    rm -f "$PORT_FILE"
    echo "Cleanup complete"
    exit $exit_code
}

# Function to start the application
start_application() {
    local port=${SYFTBOX_ASSIGNED_PORT:-9000}
    
    echo "Starting application on port $port..."
    
    # Create port file
    echo "$port" > "$PORT_FILE"
    echo "Created port file: $PORT_FILE"
    
    # Set up signal handlers
    trap cleanup_and_exit SIGINT SIGTERM
    
    # Start the application in pure blocking mode
    rm -rf .venv
    uv venv -p 3.12 .venv
    uv pip install -r requirements.txt
    uv run uvicorn backend.main:app --host 0.0.0.0 --port $port --workers 1
    
    # If we reach this point, uvicorn has stopped
    echo "Application stopped"
    cleanup_and_exit 0
}

# Main logic
echo "Checking for existing application instance..."

# Check if PID file exists (created by the application)
if [ -f "$PID_FILE" ]; then
    echo "Application is already running (PID file exists)"
    if [ -f "$PORT_FILE" ]; then
        port=$(cat "$PORT_FILE" 2>/dev/null)
        echo "Port: $port"
    fi
    echo "Use Ctrl+C to stop the application."
    exit 0
fi

# Start the application
start_application 