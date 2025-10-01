#!/usr/bin/env python3
"""Streamable HTTP server for Squber MCP server."""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import squber
sys.path.insert(0, str(Path(__file__).parent.parent))

from squber import main


def run_http_server():
    """Run Squber with Streamable HTTP transport for web access."""
    # Set environment for production HTTP mode
    os.environ["SQUBER_REQUIRE_AUTH"] = "true"  # Force auth for web access

    print("🦑 Squber - Squid Fishing AI Assistant")
    print("🌐 Starting Streamable HTTP server for web access...")
    print("🔐 Authentication required for security")
    print("📡 Using latest MCP Streamable HTTP transport (2024-11-05 spec)")

    # Run main server with Streamable HTTP transport
    main(transport="http")


if __name__ == "__main__":
    run_http_server()