#!/usr/bin/env python3
"""
Simple HTTP reverse proxy for Squber - routes /app to frontend, everything else to MCP server.
"""

import asyncio
import aiohttp
from aiohttp import web, WSMsgType
import logging

# Configuration
MCP_SERVER_URL = "http://localhost:8000"
FRONTEND_DEV_URL = "http://localhost:5173"
BACKEND_API_URL = "http://localhost:3001"
PROXY_PORT = 9000

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SquberProxy:
    def __init__(self):
        self.session = None

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def proxy_request(self, request, target_url, strip_prefix=None):
        await self.init_session()

        # Build target URL
        path = request.path_qs
        if strip_prefix and path.startswith(strip_prefix):
            path = path[len(strip_prefix):] or "/"

        full_url = f"{target_url}{path}"

        # Copy headers (exclude hop-by-hop headers)
        headers = {}
        for key, value in request.headers.items():
            if key.lower() not in ['host', 'connection', 'upgrade', 'transfer-encoding']:
                headers[key] = value

        try:
            # Make the proxied request
            async with self.session.request(
                method=request.method,
                url=full_url,
                headers=headers,
                data=await request.read() if request.can_read_body else None,
                allow_redirects=False
            ) as response:

                # Copy response headers
                resp_headers = {}
                for key, value in response.headers.items():
                    if key.lower() not in ['connection', 'transfer-encoding']:
                        resp_headers[key] = value

                # Read response body
                body = await response.read()

                return web.Response(
                    body=body,
                    status=response.status,
                    headers=resp_headers
                )

        except aiohttp.ClientError as e:
            logger.error(f"Proxy error for {full_url}: {e}")
            return web.Response(
                text=f"Proxy error: {str(e)}",
                status=502
            )

proxy = SquberProxy()

async def handle_app(request):
    """Handle /app/* requests -> frontend dev server."""
    return await proxy.proxy_request(request, FRONTEND_DEV_URL)

async def handle_api(request):
    """Handle /api/* requests -> backend API server."""
    # Check if this is a WebSocket upgrade request
    if request.headers.get('upgrade', '').lower() == 'websocket':
        return await handle_websocket_proxy(request)
    else:
        return await proxy.proxy_request(request, BACKEND_API_URL, "/api")

async def handle_websocket_proxy(request):
    """Handle WebSocket proxy to backend."""
    # Start WebSocket with client
    ws_client = web.WebSocketResponse()
    await ws_client.prepare(request)

    # Connect to backend WebSocket
    backend_ws_url = BACKEND_API_URL.replace('http://', 'ws://').replace('https://', 'wss://')

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(backend_ws_url) as backend_ws:
                # Relay messages between client and backend
                async def relay_to_backend():
                    async for msg in ws_client:
                        if msg.type == WSMsgType.TEXT:
                            await backend_ws.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await backend_ws.send_bytes(msg.data)
                        elif msg.type == WSMsgType.ERROR:
                            break

                async def relay_to_client():
                    async for msg in backend_ws:
                        if msg.type == WSMsgType.TEXT:
                            await ws_client.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_client.send_bytes(msg.data)
                        elif msg.type == WSMsgType.ERROR:
                            break

                # Run both relay tasks concurrently
                await asyncio.gather(
                    relay_to_backend(),
                    relay_to_client()
                )

    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")

    return ws_client

async def handle_mcp(request):
    """Handle everything else -> MCP server."""
    return await proxy.proxy_request(request, MCP_SERVER_URL)

async def health_check(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy",
        "proxy": "squber-reverse-proxy",
        "routes": {
            "/app/*": FRONTEND_DEV_URL,
            "/api/*": BACKEND_API_URL,
            "/*": MCP_SERVER_URL
        }
    })

async def init_app():
    app = web.Application()

    # Routes in order of specificity
    app.router.add_route('*', '/health', health_check)
    app.router.add_route('*', '/app{path:.*}', handle_app)
    app.router.add_route('*', '/api{path:.*}', handle_api)
    app.router.add_route('*', '/{path:.*}', handle_mcp)

    # Cleanup handler
    async def cleanup_context(app):
        yield
        await proxy.close_session()

    app.cleanup_ctx.append(cleanup_context)
    return app

async def main():
    app = await init_app()

    print(f"🔀 Starting Python reverse proxy on port {PROXY_PORT}")
    print(f"🎨 /app/* -> {FRONTEND_DEV_URL}")
    print(f"🖥️ /api/* -> {BACKEND_API_URL}")
    print(f"📡 /* -> {MCP_SERVER_URL}")
    print(f"❤️  Health: /health")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', PROXY_PORT)
    await site.start()

    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\n🛑 Shutting down proxy")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())