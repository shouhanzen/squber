"""Seed maritime database with realistic squid fishing data."""

import asyncio
import random
from datetime import datetime, timedelta, date
from sqlalchemy import text
from squber.database import db_manager


async def seed_ports():
    """Seed major Pacific coast squid fishing ports."""
    ports_data = [
        # California ports - major squid landing ports
        ("MNT", "Monterey", "CA", 36.6002, -121.8947, 500, True, True, "primary"),
        ("MOR", "Morro Bay", "CA", 35.3669, -120.8493, 300, True, True, "primary"),
        ("SB", "Santa Barbara", "CA", 34.4140, -119.6946, 200, True, True, "regional"),
        ("OXN", "Oxnard/Port Hueneme", "CA", 34.1478, -119.1951, 400, True, True, "primary"),
        ("LA", "Los Angeles/San Pedro", "CA", 33.7361, -118.2922, 800, True, True, "primary"),
        ("LB", "Long Beach", "CA", 33.7550, -118.1932, 300, True, True, "regional"),
        ("NWP", "Newport Beach", "CA", 33.6030, -117.9289, 100, True, True, "regional"),
        ("SD", "San Diego", "CA", 32.7157, -117.1611, 200, True, True, "regional"),

        # Oregon ports
        ("AST", "Astoria", "OR", 46.1879, -123.8306, 150, True, True, "regional"),
        ("NEW", "Newport", "OR", 44.6365, -124.0533, 200, True, True, "regional"),

        # Washington ports
        ("SEA", "Seattle", "WA", 47.6062, -122.3321, 300, True, True, "regional"),
        ("WES", "Westport", "WA", 46.9042, -124.1080, 100, True, True, "local"),
    ]

    async with db_manager.async_session() as session:
        for port in ports_data:
            await session.execute(text("""
                INSERT OR IGNORE INTO ports (port_code, port_name, state, latitude, longitude,
                                           processing_capacity, fuel_available, ice_available, market_tier)
                VALUES (:port_code, :port_name, :state, :latitude, :longitude,
                        :processing_capacity, :fuel_available, :ice_available, :market_tier)
            """), {
                "port_code": port[0],
                "port_name": port[1],
                "state": port[2],
                "latitude": port[3],
                "longitude": port[4],
                "processing_capacity": port[5],
                "fuel_available": port[6],
                "ice_available": port[7],
                "market_tier": port[8]
            })
        await session.commit()


async def seed_market_prices():
    """Seed squid market prices with seasonal patterns."""
    async with db_manager.async_session() as session:
        # Get port IDs
        result = await session.execute(text("SELECT port_id, port_code, market_tier FROM ports"))
        ports = [(row[0], row[1], row[2]) for row in result.fetchall()]

        # Generate 90 days of price data
        start_date = datetime.now().date() - timedelta(days=90)

        for day_offset in range(90):
            current_date = start_date + timedelta(days=day_offset)

            # Seasonal price adjustment - squid season peaks in winter/spring
            month = current_date.month
            if month in [11, 12, 1, 2, 3]:  # Peak season
                base_multiplier = 1.2
            elif month in [4, 5, 9, 10]:  # Shoulder season
                base_multiplier = 1.0
            else:  # Off season
                base_multiplier = 0.7

            # Weekly volatility (higher on weekends due to market dynamics)
            weekday = current_date.weekday()
            if weekday in [4, 5, 6]:  # Fri-Sun
                week_multiplier = 1.1
            else:
                week_multiplier = 1.0

            for port_id, port_code, tier in ports:
                # Tier-based pricing (primary ports get better prices)
                if tier == "primary":
                    tier_multiplier = 1.0
                elif tier == "regional":
                    tier_multiplier = 0.9
                else:  # local
                    tier_multiplier = 0.8

                # Base squid prices per grade ($/lb)
                grades = [
                    ("A", 2.50),  # Premium grade
                    ("B", 2.10),  # Standard grade
                    ("C", 1.70)   # Lower grade
                ]

                for grade, base_price in grades:
                    # Add random daily volatility (-20% to +30%)
                    volatility = random.uniform(0.8, 1.3)

                    final_price = base_price * base_multiplier * week_multiplier * tier_multiplier * volatility

                    # Generate landing volumes (higher in peak season)
                    if month in [11, 12, 1, 2, 3]:
                        volume = random.randint(10000, 50000)  # Peak season volumes
                    else:
                        volume = random.randint(1000, 15000)   # Off season volumes

                    # Supply/demand signals
                    if final_price > base_price * 1.1:
                        supply_level = "low"
                        demand_signal = "rising"
                    elif final_price < base_price * 0.9:
                        supply_level = "high"
                        demand_signal = "falling"
                    else:
                        supply_level = "normal"
                        demand_signal = "stable"

                    await session.execute(text("""
                        INSERT INTO market_prices (port_id, price_date, species, grade, price_per_lb,
                                                 volume_landed, supply_level, demand_signal)
                        VALUES (:port_id, :price_date, :species, :grade, :price_per_lb,
                                :volume_landed, :supply_level, :demand_signal)
                    """), {
                        "port_id": port_id,
                        "price_date": current_date,
                        "species": "Market Squid",
                        "grade": grade,
                        "price_per_lb": round(final_price, 4),
                        "volume_landed": volume,
                        "supply_level": supply_level,
                        "demand_signal": demand_signal
                    })

        await session.commit()


async def seed_fishing_regulations():
    """Seed current fishing regulations."""
    regulations_data = [
        ("CDFW", "season", "Market Squid", "CA", "2024-04-01", "2025-03-31",
         "California market squid season - April 1 through March 31", None, True,
         "https://wildlife.ca.gov/Conservation/Marine/Market-Squid"),
        ("CDFW", "quota", "Market Squid", "CA", "2024-04-01", "2025-03-31",
         "Weekend closure: no fishing from 12:01am Friday to 12:01am Monday", None, True, None),
        ("CDFW", "closure", "Market Squid", "Monterey Bay", "2024-04-01", "2024-04-30",
         "Closed waters within 3 nautical miles of Monterey Bay", None, True, None),
        ("NOAA", "restriction", "Market Squid", "EEZ", None, None,
         "Light restrictions: no fishing with lights > 1000 watts in EEZ", None, True,
         "https://www.fisheries.noaa.gov/species/california-market-squid"),
        ("CDFW", "quota", "Market Squid", "CA", "2024-04-01", "2025-03-31",
         "Maximum daily catch per vessel: 50 tons", 100000, True, None),  # 50 tons = 100k lbs
    ]

    async with db_manager.async_session() as session:
        for reg in regulations_data:
            await session.execute(text("""
                INSERT INTO fishing_regulations (agency, regulation_type, species, area_code,
                                               start_date, end_date, description, quota_limit,
                                               is_active, bulletin_url)
                VALUES (:agency, :regulation_type, :species, :area_code, :start_date, :end_date,
                        :description, :quota_limit, :is_active, :bulletin_url)
            """), {
                "agency": reg[0],
                "regulation_type": reg[1],
                "species": reg[2],
                "area_code": reg[3],
                "start_date": reg[4],
                "end_date": reg[5],
                "description": reg[6],
                "quota_limit": reg[7],
                "is_active": reg[8],
                "bulletin_url": reg[9]
            })
        await session.commit()


async def seed_vessels():
    """Seed fishing vessels."""
    vessels_data = [
        ("PACIFIC HUNTER", "366789120", "WDF2847", "seiner", 95, 150, 12000, 1, "Pacific Seafood Co.", True),
        ("STELLA MARIS", "366123456", "WDF2901", "seiner", 88, 120, 10000, 2, "Monterey Bay Fisheries", True),
        ("SEA WOLF", "366234567", "CF3456", "seiner", 78, 100, 8000, 3, "Morro Bay Fleet", True),
        ("OCEAN SPIRIT", "366345678", "CF4567", "jigger", 65, 80, 6000, 4, "Santa Barbara Fishing", True),
        ("BLUE FIN", "366456789", "CF5678", "seiner", 92, 140, 11000, 5, "Del Mar Seafood", True),
        ("MARIA ELENA", "366567890", "CF6789", "seiner", 85, 110, 9000, 1, "Monterey Squid Co.", True),
        ("NORTHWIND", "366678901", "OR1234", "seiner", 98, 160, 13000, 9, "Oregon Coast Fleet", True),
        ("SEAHAWK", "366789012", "WA2345", "jigger", 70, 90, 7000, 11, "Puget Sound Fishing", True),
    ]

    async with db_manager.async_session() as session:
        for vessel in vessels_data:
            await session.execute(text("""
                INSERT INTO vessels (vessel_name, mmsi, call_sign, vessel_type, length_ft,
                                   capacity_tons, fuel_capacity_gal, home_port_id, owner_operator, is_active)
                VALUES (:vessel_name, :mmsi, :call_sign, :vessel_type, :length_ft,
                        :capacity_tons, :fuel_capacity_gal, :home_port_id, :owner_operator, :is_active)
            """), {
                "vessel_name": vessel[0],
                "mmsi": vessel[1],
                "call_sign": vessel[2],
                "vessel_type": vessel[3],
                "length_ft": vessel[4],
                "capacity_tons": vessel[5],
                "fuel_capacity_gal": vessel[6],
                "home_port_id": vessel[7],
                "owner_operator": vessel[8],
                "is_active": vessel[9]
            })
        await session.commit()


async def seed_catch_reports():
    """Seed recent catch reports."""
    async with db_manager.async_session() as session:
        # Get vessel and port IDs
        vessel_result = await session.execute(text("SELECT vessel_id, vessel_type FROM vessels"))
        vessels = [(row[0], row[1]) for row in vessel_result.fetchall()]

        port_result = await session.execute(text("SELECT port_id, port_code FROM ports WHERE state='CA'"))
        ca_ports = [(row[0], row[1]) for row in port_result.fetchall()]

        # Generate 50 catch reports over last 30 days
        for _ in range(50):
            vessel_id, vessel_type = random.choice(vessels)
            port_id, port_code = random.choice(ca_ports)

            # Trip dates (1-7 day trips)
            trip_duration = random.randint(1, 7)
            trip_end = datetime.now().date() - timedelta(days=random.randint(1, 30))
            trip_start = trip_end - timedelta(days=trip_duration)

            # Catch amounts based on vessel type and season
            if vessel_type == "seiner":
                base_catch = random.randint(15000, 80000)  # Seiners catch more
            else:  # jigger
                base_catch = random.randint(5000, 25000)   # Jiggers catch less

            # Seasonal adjustment
            if trip_end.month in [11, 12, 1, 2, 3]:
                catch_multiplier = 1.3  # Peak season
            else:
                catch_multiplier = 0.6  # Off season

            pounds_landed = int(base_catch * catch_multiplier)

            # Pricing based on port market data
            grade = random.choice(["A", "B", "C"])
            if grade == "A":
                price_per_lb = round(random.uniform(2.20, 2.80), 4)
            elif grade == "B":
                price_per_lb = round(random.uniform(1.90, 2.30), 4)
            else:
                price_per_lb = round(random.uniform(1.50, 1.90), 4)

            total_revenue = pounds_landed * price_per_lb

            # Fuel usage (rough estimate)
            fuel_used = trip_duration * random.randint(800, 1500)

            fishing_areas = ["Monterey Bay", "Morro Bay", "Santa Barbara Channel",
                           "San Pedro Bay", "Catalina Island", "Point Conception"]

            await session.execute(text("""
                INSERT INTO catch_reports (vessel_id, landing_port_id, trip_start_date, trip_end_date,
                                         species, pounds_landed, grade, price_per_lb, total_revenue,
                                         fuel_used_gal, fishing_area, primary_gear, crew_count,
                                         trip_duration_hours)
                VALUES (:vessel_id, :landing_port_id, :trip_start_date, :trip_end_date, :species,
                        :pounds_landed, :grade, :price_per_lb, :total_revenue, :fuel_used_gal,
                        :fishing_area, :primary_gear, :crew_count, :trip_duration_hours)
            """), {
                "vessel_id": vessel_id,
                "landing_port_id": port_id,
                "trip_start_date": trip_start,
                "trip_end_date": trip_end,
                "species": "Market Squid",
                "pounds_landed": pounds_landed,
                "grade": grade,
                "price_per_lb": price_per_lb,
                "total_revenue": round(total_revenue, 2),
                "fuel_used_gal": fuel_used,
                "fishing_area": random.choice(fishing_areas),
                "primary_gear": "purse_seine" if vessel_type == "seiner" else "squid_jigs",
                "crew_count": random.randint(4, 8),
                "trip_duration_hours": trip_duration * 24
            })

        await session.commit()


async def seed_demand_signals():
    """Seed market demand signals."""
    signals_data = [
        ("2024-12-20", "festival", "Asia", "Chinese New Year preparation - increased squid demand",
         "high", "positive", 45, 0.9, None),
        ("2024-11-15", "export", "Asia", "Japanese market opens for premium grade imports",
         "medium", "positive", 30, 0.7, None),
        ("2024-10-01", "quota", "US_West", "California quota increased by 15% for remainder of season",
         "medium", "negative", 180, 0.8, "https://wildlife.ca.gov/bulletins"),
        ("2024-09-15", "weather", "US_West", "El Niño conditions affecting squid migration patterns",
         "high", "negative", 120, 0.6, "https://noaa.gov/weather"),
        ("2024-12-01", "festival", "Europe", "Holiday season increases Mediterranean squid imports",
         "medium", "positive", 60, 0.8, None),
    ]

    async with db_manager.async_session() as session:
        for signal in signals_data:
            await session.execute(text("""
                INSERT INTO demand_signals (signal_date, signal_type, region, description,
                                          impact_level, price_impact, duration_days, confidence_level, source_url)
                VALUES (:signal_date, :signal_type, :region, :description, :impact_level,
                        :price_impact, :duration_days, :confidence_level, :source_url)
            """), {
                "signal_date": signal[0],
                "signal_type": signal[1],
                "region": signal[2],
                "description": signal[3],
                "impact_level": signal[4],
                "price_impact": signal[5],
                "duration_days": signal[6],
                "confidence_level": signal[7],
                "source_url": signal[8]
            })
        await session.commit()


async def seed_maritime_database():
    """Seed the database with all maritime data."""
    print("Seeding ports...")
    await seed_ports()

    print("Seeding market prices...")
    await seed_market_prices()

    print("Seeding fishing regulations...")
    await seed_fishing_regulations()

    print("Seeding vessels...")
    await seed_vessels()

    print("Seeding catch reports...")
    await seed_catch_reports()

    print("Seeding demand signals...")
    await seed_demand_signals()

    print("Maritime database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_maritime_database())