"""HTTP server wrapper for Squber MCP server to enable ngrok forwarding."""

import asyncio
import json
import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



class SquberHTTPServer:
    """HTTP wrapper for Squber MCP server."""

    def __init__(self):
        self.app = FastAPI(
            title="Squber - Squid Fishing AI Assistant API",
            description="HTTP API for Squber MCP Server",
            version="0.1.0"
        )

        # Enable CORS for web access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.setup_routes()

    def setup_routes(self):
        """Set up HTTP routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "name": "Squber - Squid Fishing AI Assistant API",
                "version": "0.1.0",
                "description": "HTTP API for MCP server providing squid fishing market intelligence",
                "endpoints": {
                    "/tools/list": "List available MCP tools",
                    "/tools/{tool_name}": "Execute MCP tool",
                    "/health": "Server health check"
                }
            }

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "squber-mcp-api"}


        @self.app.post("/tools/{tool_name}")
        async def execute_tool(
            tool_name: str,
            request: Request
        ):
            """Execute an MCP tool."""
            try:
                # Parse request body for tool parameters
                body = await request.json() if request.headers.get("content-type") == "application/json" else {}

                # Execute MCP tool via STDIO client
                result = await self.execute_mcp_tool(tool_name, body)
                return JSONResponse(content=result)

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/tools/list")
        async def list_tools():
            """List available MCP tools."""
            try:
                tools = await self.list_mcp_tools()
                return JSONResponse(content={"tools": tools})
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Non-MCP routes for serving frontend
        @self.app.get("/frontend")
        async def frontend_redirect():
            """Redirect to frontend app."""
            return JSONResponse(content={
                "message": "Frontend available at /app",
                "frontend_url": "/app",
                "api_docs": "/docs"
            })

        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        import os

        # Serve static frontend files (if built)
        frontend_dist = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
        if os.path.exists(frontend_dist):
            self.app.mount("/app", StaticFiles(directory=frontend_dist, html=True), name="frontend")

            @self.app.get("/app/{full_path:path}")
            async def serve_frontend(full_path: str):
                """Serve React frontend with fallback to index.html for SPA routing."""
                file_path = os.path.join(frontend_dist, full_path)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    return FileResponse(file_path)
                # Fallback to index.html for SPA routing
                return FileResponse(os.path.join(frontend_dist, "index.html"))

    async def execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool via STDIO client."""
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "squber"],
            env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Execute the tool
                result = await session.call_tool(tool_name, parameters)

                # Parse JSON response if possible
                try:
                    return {
                        "tool": tool_name,
                        "parameters": parameters,
                        "result": json.loads(result.content[0].text) if result.content else {},
                        "status": "success"
                    }
                except json.JSONDecodeError:
                    return {
                        "tool": tool_name,
                        "parameters": parameters,
                        "result": result.content[0].text if result.content else "",
                        "status": "success"
                    }

    async def list_mcp_tools(self) -> list:
        """List available MCP tools."""
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "squber"],
            env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools.tools
                ]

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the HTTP server."""
        print(f"🦑 Starting Squber HTTP API server on {host}:{port}")
        print(f"🌍 Environment: {os.getenv('SQUBER_ENV', 'development')}")

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


def main():
    """Run HTTP server."""
    server = SquberHTTPServer()
    host = os.getenv("SQUBER_HOST", "0.0.0.0")
    port = int(os.getenv("SQUBER_PORT", 8000))
    server.run(host=host, port=port)


if __name__ == "__main__":
    main()