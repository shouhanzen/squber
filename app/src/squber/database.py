"""Database connection and utilities for Squber."""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, inspect
import pandas as pd


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "squber.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}",
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def execute_query(self, query: str, limit: int = 1000, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a readonly SQL query with optional parameters."""
        # Basic safety check - only allow SELECT statements
        query_stripped = query.strip().upper()
        if not query_stripped.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        # Add LIMIT if not present
        if "LIMIT" not in query_stripped:
            query += f" LIMIT {limit}"

        async with self.async_session() as session:
            if params:
                result = await session.execute(text(query), params)
            else:
                result = await session.execute(text(query))
            rows = result.fetchall()
            columns = list(result.keys()) if rows else []

            return {
                "columns": columns,
                "rows": [dict(zip(columns, row)) for row in rows],
                "row_count": len(rows),
                "query": query
            }

    async def get_schema(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get database schema information."""
        schema_info = {"tables": {}}

        async with self.async_session() as session:
            # Get all table names
            result = await session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ))
            tables = [row[0] for row in result.fetchall()]

            for table in tables:
                if table_name and table != table_name:
                    continue

                # Get column information
                result = await session.execute(text(f"PRAGMA table_info({table})"))
                columns = []
                for row in result.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],
                        "default": row[4],
                        "primary_key": bool(row[5])
                    })

                # Get row count
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                row_count = result.fetchone()[0]

                schema_info["tables"][table] = {
                    "columns": columns,
                    "row_count": row_count
                }

        return schema_info

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()