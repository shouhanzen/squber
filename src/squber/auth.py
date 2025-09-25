"""Authentication module for Squber MCP server."""

import os
import secrets
import hashlib
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SquberAuth:
    """Simple API key authentication for Squber MCP server."""

    def __init__(self):
        self.api_key = os.getenv("SQUBER_API_KEY", "squid-fishing-captain-2024-secure-key-123")
        self.secret = os.getenv("SQUBER_SECRET", "your-secret-key-change-in-production")

        # In production, these should be stored securely and rotated regularly
        self.valid_keys = {
            self.api_key: {
                "name": "Captain Access",
                "permissions": ["read", "market_report", "trip_advisor"],
                "active": True
            }
        }

    def validate_api_key(self, api_key: Optional[str]) -> bool:
        """Validate provided API key."""
        if not api_key:
            return False

        return api_key in self.valid_keys and self.valid_keys[api_key]["active"]

    def get_key_info(self, api_key: str) -> dict:
        """Get information about the API key."""
        return self.valid_keys.get(api_key, {})

    def generate_new_key(self, name: str, permissions: list) -> str:
        """Generate a new API key (for admin use)."""
        new_key = f"squber-{secrets.token_urlsafe(32)}"
        self.valid_keys[new_key] = {
            "name": name,
            "permissions": permissions,
            "active": True
        }
        return new_key

    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.valid_keys:
            self.valid_keys[api_key]["active"] = False
            return True
        return False


# Global auth instance
squber_auth = SquberAuth()


def require_auth(api_key: Optional[str]) -> bool:
    """Check if request is authenticated."""
    return squber_auth.validate_api_key(api_key)


def get_auth_info() -> dict:
    """Get authentication information for display."""
    return {
        "auth_required": True,
        "auth_method": "API Key",
        "header_name": "X-API-Key",
        "environment_var": "SQUBER_API_KEY",
        "sample_key": squber_auth.api_key[:20] + "..." if squber_auth.api_key else None
    }