#!/bin/bash

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uv run squber" || true
pkill -f "npm run dev" || true
pkill -f "nginx" || true
pkill -f "ngrok http" || true
pkill -f "vite" || true
pkill -f "proxy.py" || true

# Wait a moment for cleanup
sleep 2

echo "🚀 Starting Squber MCP server on port 8000..."
# Start MCP server
export SQUBER_PORT=8000
export SQUBER_ENV=development
uv run squber-http &
MCP_PID=$!

echo "🖥️ Starting Node.js backend on port 3001..."
# Install backend dependencies if needed
if [ ! -d "backend/node_modules" ]; then
    echo "📦 Installing backend dependencies..."
    cd backend && npm install && cd ..
fi
# Start backend
cd backend && npm start &
BACKEND_PID=$!
cd ..

echo "🎨 Starting frontend dev server on port 5173..."
# Start frontend dev server
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if ! ps -p $MCP_PID > /dev/null; then
    echo "❌ MCP server failed to start"
    exit 1
fi

if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend server failed to start"
    exit 1
fi

if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "❌ Frontend server failed to start"
    exit 1
fi

echo "🔀 Starting Python reverse proxy on port 9000..."
# Start Python proxy
cd squber
uv run python proxy.py &
PROXY_PID=$!

# Wait for proxy
sleep 2

if ! ps -p $PROXY_PID > /dev/null; then
    echo "❌ Proxy failed to start"
    exit 1
fi

echo "✅ All services started successfully"
echo "   📡 MCP Server: localhost:8000"
echo "   🖥️ Backend: localhost:3001"
echo "   🎨 Frontend: localhost:5173"
echo "   🔀 Python Proxy: localhost:9000"
echo ""
echo "🌐 Starting ngrok tunnel..."

# Start ngrok
ngrok http 9000 --log stdout

# Cleanup on exit
trap "kill $MCP_PID $BACKEND_PID $FRONTEND_PID $PROXY_PID 2>/dev/null || true" EXIT