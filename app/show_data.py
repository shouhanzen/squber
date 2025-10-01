#!/usr/bin/env python3
"""Show squid fishing maritime database contents."""

import asyncio
from src.squber.database import db_manager


async def show_maritime_data():
    """Display maritime squid fishing data in the database."""

    print("🦑 " + "=" * 58)
    print("   SQUID FISHING MARITIME DATABASE CONTENTS")
    print("=" * 60)

    # Get schema first - focus on maritime tables only
    schema = await db_manager.get_schema()
    maritime_tables = [
        "ports", "market_prices", "fishing_regulations", "vessels",
        "catch_reports", "demand_signals", "environmental_data"
    ]

    for table_name in maritime_tables:
        if table_name in schema["tables"]:
            table_info = schema["tables"][table_name]
            print(f"\n🐙 TABLE: {table_name.upper()}")
            print(f"   Columns: {len(table_info['columns'])}")
            print(f"   Rows: {table_info['row_count']}")

            # Show sample data for key maritime tables
            if table_info['row_count'] > 0 and table_name in ["ports", "market_prices", "fishing_regulations", "vessels"]:
                query = f"SELECT * FROM {table_name} LIMIT 3"
                result = await db_manager.execute_query(query)

                print("   Sample data:")
                for i, row in enumerate(result['rows'], 1):
                    # Show abbreviated data for readability
                    if table_name == "market_prices":
                        print(f"     {i}. Port: {row.get('port_id')}, Date: {row.get('price_date')}, Grade: {row.get('grade')}, Price: ${row.get('price_per_lb')}/lb")
                    elif table_name == "ports":
                        print(f"     {i}. {row.get('port_name')} ({row.get('port_code')}), {row.get('state')} - {row.get('market_tier')} tier")
                    elif table_name == "vessels":
                        print(f"     {i}. {row.get('vessel_name')} - {row.get('vessel_type')}, {row.get('capacity_tons')} tons")
                    else:
                        print(f"     {i}. {str(row)[:100]}...")
            print()

    # Show fishing-specific insights
    print("🎯 SQUID FISHING INSIGHTS:")

    fishing_queries = [
        ("Major California Ports", """
            SELECT port_name, processing_capacity, market_tier
            FROM ports
            WHERE state = 'CA'
            ORDER BY processing_capacity DESC
            LIMIT 5
        """),
        ("Current Market Prices (Grade A)", """
            SELECT p.port_name, mp.price_per_lb, mp.supply_level
            FROM market_prices mp
            JOIN ports p ON mp.port_id = p.port_id
            WHERE mp.grade = 'A' AND mp.price_date >= date('now', '-3 days')
            ORDER BY mp.price_per_lb DESC
            LIMIT 5
        """),
        ("Active Fishing Fleet", """
            SELECT vessel_name, vessel_type, capacity_tons, v.home_port_id, p.port_name
            FROM vessels v
            JOIN ports p ON v.home_port_id = p.port_id
            WHERE v.is_active = 1
            ORDER BY capacity_tons DESC
        """),
        ("Recent Best Catches", """
            SELECT v.vessel_name, cr.pounds_landed, cr.total_revenue, cr.fishing_area, cr.trip_end_date
            FROM catch_reports cr
            JOIN vessels v ON cr.vessel_id = v.vessel_id
            ORDER BY cr.pounds_landed DESC
            LIMIT 5
        """),
        ("Current Regulations", """
            SELECT regulation_type, area_code, description
            FROM fishing_regulations
            WHERE is_active = 1 AND species = 'Market Squid'
            ORDER BY regulation_type
        """)
    ]

    for title, query in fishing_queries:
        print(f"\n🔍 {title}:")
        try:
            result = await db_manager.execute_query(query)
            for i, row in enumerate(result['rows'], 1):
                if title == "Current Market Prices (Grade A)":
                    print(f"  {i}. {row['port_name']}: ${row['price_per_lb']:.2f}/lb ({row['supply_level']} supply)")
                elif title == "Recent Best Catches":
                    print(f"  {i}. {row['vessel_name']}: {row['pounds_landed']:,} lbs = ${row['total_revenue']:,.0f} ({row['fishing_area']})")
                elif title == "Major California Ports":
                    print(f"  {i}. {row['port_name']}: {row['processing_capacity']} tons/day ({row['market_tier']})")
                else:
                    # Show first few key fields for other queries
                    key_fields = list(row.keys())[:3]
                    display = ", ".join([f"{k}: {row[k]}" for k in key_fields])
                    print(f"  {i}. {display}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n🚢 CAPTAIN DECISION SUPPORT:")
    print("This database helps answer the key questions:")
    print("  1. When should I leave port? (market prices, regulations, demand signals)")
    print("  2. When should I return? (price trends, fleet activity)")
    print("  3. Which port should I land in? (port comparison, processing capacity)")

    print(f"\n📊 Total maritime records: {sum(schema['tables'][t]['row_count'] for t in maritime_tables if t in schema['tables'])}")


if __name__ == "__main__":
    asyncio.run(show_maritime_data())