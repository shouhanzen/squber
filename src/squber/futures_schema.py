"""Futures market database schema for squid trading."""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from .database import db_manager


async def create_futures_tables():
    """Create futures trading tables."""
    async with db_manager.async_session() as session:

        # Futures contracts table - contract specifications
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS futures_contracts (
                contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,           -- 'SQ-MAR25', 'SQ-JUN25'
                contract_type TEXT NOT NULL,           -- 'monthly', 'quarterly'
                delivery_month TEXT NOT NULL,          -- '2025-03', '2025-Q2'
                expiry_date DATE NOT NULL,
                contract_size_tons INTEGER NOT NULL,   -- 50 tons standard
                delivery_port_id INTEGER,              -- FK to ports (NULL = cash settled)
                grade TEXT NOT NULL,                   -- 'A', 'B', 'C'
                tick_size REAL NOT NULL DEFAULT 0.01,  -- 0.01 (1 cent)
                created_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'active', -- 'active', 'expired', 'delivered'
                settlement_type TEXT DEFAULT 'physical', -- 'physical', 'cash'
                FOREIGN KEY (delivery_port_id) REFERENCES ports(port_id)
            )
        """))

        # Futures prices table - daily price data
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS futures_prices (
                price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                trade_date DATE NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                settle_price REAL NOT NULL,            -- Daily settlement price
                volume INTEGER DEFAULT 0,              -- Contracts traded
                open_interest INTEGER DEFAULT 0,       -- Outstanding positions
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES futures_contracts(contract_id),
                UNIQUE(contract_id, trade_date)
            )
        """))

        # Futures positions table - captain holdings
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS futures_positions (
                position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vessel_id INTEGER NOT NULL,
                contract_id INTEGER NOT NULL,
                position_type TEXT NOT NULL,           -- 'long' (buy), 'short' (sell)
                quantity INTEGER NOT NULL,             -- Number of contracts
                entry_price REAL NOT NULL,
                entry_date DATE NOT NULL,
                exit_price REAL,
                exit_date DATE,
                status TEXT NOT NULL DEFAULT 'open',   -- 'open', 'closed', 'delivered'
                margin_requirement REAL,              -- Required margin
                unrealized_pnl REAL DEFAULT 0,        -- Mark-to-market P&L
                realized_pnl REAL DEFAULT 0,          -- Closed position P&L
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vessel_id) REFERENCES vessels(vessel_id),
                FOREIGN KEY (contract_id) REFERENCES futures_contracts(contract_id)
            )
        """))

        # Futures settlements table - delivery tracking
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS futures_settlements (
                settlement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                vessel_id INTEGER NOT NULL,
                position_id INTEGER,                   -- FK to position
                settlement_type TEXT NOT NULL,         -- 'physical', 'cash'
                delivery_port_id INTEGER,              -- Actual delivery port
                delivery_date DATE,
                physical_quantity_tons REAL,           -- Actual delivery amount
                cash_settlement_amount REAL,           -- Cash settlement value
                final_price REAL NOT NULL,             -- Final settlement price
                grade_delivered TEXT,                  -- Actual grade delivered
                settlement_date DATE NOT NULL,
                quality_adjustment REAL DEFAULT 0,     -- Price adjustment for quality
                FOREIGN KEY (contract_id) REFERENCES futures_contracts(contract_id),
                FOREIGN KEY (vessel_id) REFERENCES vessels(vessel_id),
                FOREIGN KEY (position_id) REFERENCES futures_positions(position_id),
                FOREIGN KEY (delivery_port_id) REFERENCES ports(port_id)
            )
        """))

        # Create performance indexes
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_futures_prices_contract_date
            ON futures_prices(contract_id, trade_date)
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_positions_vessel_status
            ON futures_positions(vessel_id, status)
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contracts_expiry
            ON futures_contracts(expiry_date, status)
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contracts_symbol
            ON futures_contracts(symbol)
        """))

        await session.commit()
        print("Futures tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_futures_tables())