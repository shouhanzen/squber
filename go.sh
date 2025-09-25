#!/bin/bash

# Kill any existing processes on port 8001
echo "🧹 Cleaning up existing processes..."
pkill -f "uv run squber" || true
pkill -f "ngrok http 8001" || true

# Wait a moment for cleanup
sleep 2

echo "🚀 Starting Squber HTTP server on port 8001..."

# Set port environment variable and start the HTTP server
export SQUBER_PORT=8001
uv run squber-http &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Check if server is running
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Server failed to start"
    exit 1
fi

echo "✅ Server started successfully (PID: $SERVER_PID)"
echo "🌐 Starting ngrok tunnel..."

# Start ngrok
ngrok http 8001 --log stdout

# Cleanup on exit
trap "kill $SERVER_PID 2>/dev/null || true" EXIT