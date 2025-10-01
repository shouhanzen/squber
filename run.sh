#!/bin/bash

cd app

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uv run squber" || true
pkill -f "ngrok http" || true

# Wait a moment for cleanup
sleep 2

echo "🚀 Starting Squber MCP server on port 8000..."
# Start MCP server
export SQUBER_PORT=8000
export SQUBER_ENV=development
uv run squber-http &
MCP_PID=$!

# Wait for service to start
echo "⏳ Waiting for MCP server to start..."
sleep 3

# Check if service is running
if ! ps -p $MCP_PID > /dev/null; then
    echo "❌ MCP server failed to start"
    exit 1
fi

echo "✅ MCP server started successfully"
echo "   📡 MCP Server: localhost:8000"
echo ""
echo "🌐 Starting ngrok tunnel..."

# Start ngrok
ngrok http 8000 --log stdout

# Cleanup on exit
trap "kill $MCP_PID 2>/dev/null || true" EXIT