import fastmcp
from typing import Any, Optional
import json
import asyncio
import os
from datetime import datetime, timedelta, date
from .database import db_manager
from .auth import require_auth, get_auth_info, squber_auth


# Create MCP server - Squid Catchers AI Assistant
mcp = fastmcp.FastMCP("Squber - Squid Fishing AI Assistant")


def auth_middleware(context: dict) -> bool:
    """Authentication middleware for MCP requests."""
    # For STDIO mode (local development), skip auth
    if os.getenv("SQUBER_ENV") == "development" and not os.getenv("SQUBER_REQUIRE_AUTH"):
        return True

    # Extract API key from context/headers
    api_key = context.get("headers", {}).get("x-api-key") or context.get("api_key")

    if not require_auth(api_key):
        raise PermissionError("Invalid or missing API key. Please provide a valid X-API-Key header.")

    return True


@mcp.tool()
async def query_data(query: str, limit: int = 1000) -> str:
    """Execute a readonly SQL query against the maritime database.

    Args:
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return (default: 1000)

    Returns:
        JSON formatted query results with columns, rows, and metadata
    """
    try:
        # Validate that this is a SELECT query
        if not query.strip().upper().startswith("SELECT"):
            return json.dumps({
                "error": "Only SELECT queries are allowed",
                "query": query
            })

        result = await db_manager.execute_query(query, limit)

        return json.dumps({
            "success": True,
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
            "query": result["query"]
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "query": query
        })


@mcp.tool()
async def squber_howto(table_name: Optional[str] = None) -> str:
    """Get maritime database schema and example queries for squid fishing analysis.

    Args:
        table_name: Optional specific table name to get schema for.
                   If not provided, returns schema for all tables.

    Returns:
        JSON formatted schema information with fishing-specific examples
    """
    try:
        schema = await db_manager.get_schema(table_name)

        # Add fishing-specific information
        help_info = {
            "database_info": {
                "tables": list(schema["tables"].keys()),
                "total_tables": len(schema["tables"]),
                "description": "Maritime squid fishing database with market, regulatory, and fleet data"
            },
            "key_questions": [
                "When should I leave port?",
                "When should I return?",
                "Which port should I land in?"
            ],
            "example_queries": [
                # Market intelligence
                "SELECT port_name, price_per_lb, supply_level FROM market_prices mp JOIN ports p ON mp.port_id = p.port_id WHERE price_date = CURRENT_DATE AND grade = 'A' ORDER BY price_per_lb DESC",

                # Regulatory status
                "SELECT * FROM fishing_regulations WHERE species = 'Market Squid' AND is_active = 1",

                # Fleet activity
                "SELECT v.vessel_name, cr.pounds_landed, cr.total_revenue, cr.trip_end_date FROM catch_reports cr JOIN vessels v ON cr.vessel_id = v.vessel_id ORDER BY cr.trip_end_date DESC LIMIT 10",

                # Port comparison
                "SELECT p.port_name, AVG(mp.price_per_lb) as avg_price, SUM(mp.volume_landed) as total_volume FROM market_prices mp JOIN ports p ON mp.port_id = p.port_id WHERE mp.price_date >= date('now', '-7 days') GROUP BY p.port_id ORDER BY avg_price DESC",

                # Demand signals
                "SELECT * FROM demand_signals WHERE signal_date >= date('now', '-30 days') AND price_impact = 'positive' ORDER BY confidence_level DESC"
            ],
            "schema": schema
        }

        return json.dumps(help_info, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "table_name": table_name
        })


@mcp.tool()
async def get_market_report(days: int = 7, port_codes: Optional[str] = None) -> str:
    """Get current market conditions and price trends for squid fishing.

    Args:
        days: Number of days to analyze (default: 7)
        port_codes: Comma-separated port codes to focus on (e.g., "MNT,MOR,SB")

    Returns:
        Market intelligence report with pricing trends and recommendations
    """
    try:
        # Build port filter
        port_filter = ""
        if port_codes:
            codes = [f"'{code.strip()}'" for code in port_codes.split(',')]
            port_filter = f"AND p.port_code IN ({','.join(codes)})"

        # Get recent price trends
        price_query = f"""
        SELECT p.port_name, p.port_code, mp.grade,
               AVG(mp.price_per_lb) as avg_price,
               SUM(mp.volume_landed) as total_volume,
               mp.supply_level, mp.demand_signal
        FROM market_prices mp
        JOIN ports p ON mp.port_id = p.port_id
        WHERE mp.price_date >= date('now', '-{days} days') {port_filter}
        GROUP BY p.port_id, mp.grade
        ORDER BY p.port_code, mp.grade
        """

        price_result = await db_manager.execute_query(price_query)

        # Get active regulations
        reg_query = """
        SELECT regulation_type, area_code, description,
               start_date, end_date, is_active
        FROM fishing_regulations
        WHERE species = 'Market Squid' AND is_active = 1
        ORDER BY regulation_type
        """

        reg_result = await db_manager.execute_query(reg_query)

        # Get recent demand signals
        demand_query = f"""
        SELECT signal_type, region, description, impact_level,
               price_impact, confidence_level, signal_date
        FROM demand_signals
        WHERE signal_date >= date('now', '-{days} days')
        ORDER BY confidence_level DESC, signal_date DESC
        """

        demand_result = await db_manager.execute_query(demand_query)

        # Generate recommendations based on data
        recommendations = []

        if price_result["rows"]:
            # Find best ports by grade A pricing
            grade_a_ports = [row for row in price_result["rows"] if row.get("grade") == "A"]
            if grade_a_ports:
                best_port = max(grade_a_ports, key=lambda x: x["avg_price"])
                recommendations.append(f"Best Grade A pricing at {best_port['port_name']} (${best_port['avg_price']:.2f}/lb)")

        if demand_result["rows"]:
            positive_signals = [row for row in demand_result["rows"] if row.get("price_impact") == "positive"]
            if positive_signals:
                recommendations.append(f"Market outlook positive: {positive_signals[0]['description']}")

        report = {
            "report_date": datetime.now().isoformat(),
            "analysis_period_days": days,
            "market_prices": price_result["rows"],
            "active_regulations": reg_result["rows"],
            "demand_signals": demand_result["rows"],
            "recommendations": recommendations,
            "summary": f"Analyzed {len(price_result['rows'])} price points across {days} days"
        }

        return json.dumps(report, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "days": days,
            "port_codes": port_codes
        })


@mcp.tool()
async def trip_advisor(vessel_name: Optional[str] = None, target_port: Optional[str] = None) -> str:
    """Get trip planning advice for squid fishing operations.

    Args:
        vessel_name: Name of vessel planning the trip
        target_port: Preferred landing port code

    Returns:
        Trip planning recommendations with timing and port suggestions
    """
    try:
        recommendations = []

        # Get current market conditions
        market_query = """
        SELECT p.port_name, p.port_code, mp.price_per_lb, mp.supply_level,
               p.processing_capacity, p.market_tier
        FROM market_prices mp
        JOIN ports p ON mp.port_id = p.port_id
        WHERE mp.price_date = date('now') AND mp.grade = 'A'
        ORDER BY mp.price_per_lb DESC
        LIMIT 5
        """

        market_result = await db_manager.execute_query(market_query)

        # Check regulations
        reg_query = """
        SELECT description, area_code, end_date
        FROM fishing_regulations
        WHERE species = 'Market Squid' AND is_active = 1
        AND regulation_type IN ('closure', 'restriction')
        """

        reg_result = await db_manager.execute_query(reg_query)

        # Get recent fleet performance
        fleet_query = """
        SELECT v.vessel_name, cr.pounds_landed, cr.fishing_area,
               cr.trip_end_date, p.port_name
        FROM catch_reports cr
        JOIN vessels v ON cr.vessel_id = v.vessel_id
        JOIN ports p ON cr.landing_port_id = p.port_id
        WHERE cr.trip_end_date >= date('now', '-7 days')
        ORDER BY cr.pounds_landed DESC
        LIMIT 10
        """

        fleet_result = await db_manager.execute_query(fleet_query)

        # Generate recommendations
        if market_result["rows"]:
            best_markets = market_result["rows"][:3]
            recommendations.append("TOP MARKETS TODAY:")
            for i, market in enumerate(best_markets, 1):
                recommendations.append(f"{i}. {market['port_name']}: ${market['price_per_lb']:.2f}/lb ({market['supply_level']} supply)")

        if reg_result["rows"]:
            recommendations.append("\nREGULATORY ALERTS:")
            for reg in reg_result["rows"][:3]:
                recommendations.append(f"• {reg['description']}")

        if fleet_result["rows"]:
            top_areas = {}
            for trip in fleet_result["rows"]:
                area = trip["fishing_area"]
                if area in top_areas:
                    top_areas[area] += trip["pounds_landed"]
                else:
                    top_areas[area] = trip["pounds_landed"]

            if top_areas:
                best_area = max(top_areas, key=top_areas.get)
                recommendations.append(f"\nHOT FISHING AREAS: {best_area} (recent fleet success)")

        # Timing recommendations
        current_date = datetime.now()
        if current_date.weekday() in [3, 4]:  # Thursday/Friday
            recommendations.append("\nTIMING: Consider weekend closure - plan return by Friday midnight")

        advice = {
            "vessel_query": vessel_name,
            "target_port": target_port,
            "generated_at": current_date.isoformat(),
            "recommendations": recommendations,
            "current_markets": market_result["rows"],
            "active_restrictions": reg_result["rows"],
            "recent_fleet_success": fleet_result["rows"]
        }

        return json.dumps(advice, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "vessel_name": vessel_name,
            "target_port": target_port
        })


@mcp.tool()
async def auth_status() -> str:
    """Get authentication status and configuration information."""
    try:
        auth_info = get_auth_info()

        status = {
            "authentication": {
                "enabled": auth_info["auth_required"],
                "method": auth_info["auth_method"],
                "header_required": auth_info["header_name"],
                "environment": os.getenv("SQUBER_ENV", "development")
            },
            "server_info": {
                "name": "Squber - Squid Fishing AI Assistant",
                "version": "0.1.0",
                "database": "SQLite with squid fishing maritime data",
                "total_captains_served": "Awaiting first authenticated connection"
            },
            "usage": {
                "api_key_format": "X-API-Key: your-api-key-here",
                "sample_key": auth_info.get("sample_key", "Contact admin for API key"),
                "note": "API key required for production access"
            }
        }

        return json.dumps(status, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "authentication_check_failed"
        })


@mcp.resource("config://settings")
def get_settings() -> dict[str, Any]:
    """Get application settings."""
    return {
        "app_name": "squber",
        "version": "0.1.0",
        "environment": os.getenv("SQUBER_ENV", "development"),
        "database": "SQLite with squid fishing maritime data",
        "description": "AI Assistant for Squid Fishers - Market Intelligence & Trip Planning",
        "authentication": get_auth_info()
    }


def main(transport: str = "stdio") -> None:
    """Run the FastMCP server."""
    if transport == "http":
        # Run with Streamable HTTP transport (recommended for web access)
        host = os.getenv("SQUBER_HOST", "0.0.0.0")
        port = int(os.getenv("SQUBER_PORT", 8000))

        print(f"🦑 Starting Squber with Streamable HTTP on http://{host}:{port}")
        print(f"🔐 Authentication: {get_auth_info()['auth_method']}")
        print(f"🌍 Environment: {os.getenv('SQUBER_ENV', 'development')}")
        print(f"🌐 MCP Endpoint: http://{host}:{port}/ (single endpoint)")
        print(f"📡 Transport: Streamable HTTP (MCP 2024-11-05 spec)")

        mcp.run(transport="http", host=host, port=port)
    else:
        # Default STDIO transport
        mcp.run()
