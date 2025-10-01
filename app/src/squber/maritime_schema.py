"""Maritime database schema for squid fishing data."""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from .database import db_manager


async def create_maritime_tables():
    """Create maritime/fishing tables."""
    async with db_manager.async_session() as session:

        # Ports table - fishing ports and facilities
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS ports (
                port_id INTEGER PRIMARY KEY AUTOINCREMENT,
                port_code TEXT UNIQUE NOT NULL,
                port_name TEXT NOT NULL,
                state TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                processing_capacity INTEGER DEFAULT 0,  -- tons per day
                fuel_available BOOLEAN DEFAULT 1,
                ice_available BOOLEAN DEFAULT 1,
                market_tier TEXT DEFAULT 'regional',  -- primary, regional, local
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Market prices table - squid prices by port and date
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS market_prices (
                price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                port_id INTEGER,
                price_date DATE NOT NULL,
                species TEXT NOT NULL,
                grade TEXT NOT NULL,  -- A, B, C quality grades
                price_per_lb DECIMAL(8,4) NOT NULL,
                volume_landed INTEGER DEFAULT 0,  -- pounds
                supply_level TEXT DEFAULT 'normal',  -- low, normal, high
                demand_signal TEXT DEFAULT 'stable',  -- rising, stable, falling
                FOREIGN KEY (port_id) REFERENCES ports(port_id)
            )
        """))

        # Fishing regulations table - active rules and closures
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS fishing_regulations (
                regulation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency TEXT NOT NULL,  -- CDFW, NOAA, etc.
                regulation_type TEXT NOT NULL,  -- closure, quota, restriction
                species TEXT NOT NULL,
                area_code TEXT,  -- fishing area identifier
                start_date DATE,
                end_date DATE,
                description TEXT,
                quota_limit INTEGER,  -- if applicable, in pounds
                is_active BOOLEAN DEFAULT 1,
                bulletin_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Vessels table - fishing vessel information
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS vessels (
                vessel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vessel_name TEXT NOT NULL,
                mmsi TEXT UNIQUE,  -- Maritime Mobile Service Identity
                call_sign TEXT,
                vessel_type TEXT DEFAULT 'seiner',  -- seiner, jigger
                length_ft INTEGER,
                capacity_tons INTEGER,
                fuel_capacity_gal INTEGER,
                home_port_id INTEGER,
                owner_operator TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (home_port_id) REFERENCES ports(port_id)
            )
        """))

        # Vessel positions table - AIS tracking data
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS vessel_positions (
                position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vessel_id INTEGER,
                timestamp TIMESTAMP NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                speed_knots REAL,
                heading INTEGER,  -- degrees
                activity_type TEXT,  -- transit, fishing, returning
                fishing_area TEXT,  -- area code if fishing
                FOREIGN KEY (vessel_id) REFERENCES vessels(vessel_id)
            )
        """))

        # Catch reports table - landing records
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS catch_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vessel_id INTEGER,
                landing_port_id INTEGER,
                trip_start_date DATE,
                trip_end_date DATE,
                species TEXT NOT NULL,
                pounds_landed INTEGER NOT NULL,
                grade TEXT,
                price_per_lb DECIMAL(8,4),
                total_revenue DECIMAL(12,2),
                fuel_used_gal INTEGER,
                fishing_area TEXT,
                primary_gear TEXT,  -- purse_seine, jigs, etc.
                crew_count INTEGER,
                trip_duration_hours INTEGER,
                FOREIGN KEY (vessel_id) REFERENCES vessels(vessel_id),
                FOREIGN KEY (landing_port_id) REFERENCES ports(port_id)
            )
        """))

        # Environmental data table - conditions affecting fishing
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS environmental_data (
                env_id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_date DATE NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                sea_temp_f REAL,
                current_speed_kts REAL,
                current_direction INTEGER,  -- degrees
                wind_speed_kts REAL,
                wind_direction INTEGER,
                moon_phase REAL,  -- 0-1, 0=new moon, 0.5=full moon
                chlorophyll_level REAL,  -- indicator of food chain
                area_code TEXT,
                data_source TEXT DEFAULT 'NOAA'
            )
        """))

        # Demand signals table - market intelligence
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS demand_signals (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_date DATE NOT NULL,
                signal_type TEXT NOT NULL,  -- festival, export, quota, weather
                region TEXT,  -- Asia, Europe, US_West, US_East
                description TEXT,
                impact_level TEXT DEFAULT 'medium',  -- low, medium, high
                price_impact TEXT DEFAULT 'neutral',  -- positive, neutral, negative
                duration_days INTEGER,
                confidence_level REAL DEFAULT 0.5,  -- 0-1 confidence score
                source_url TEXT
            )
        """))

        await session.commit()
        print("Maritime tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_maritime_tables())