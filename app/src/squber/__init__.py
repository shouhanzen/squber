import fastmcp
from typing import Any, Optional
import json
import asyncio
import os
from datetime import datetime, timedelta, date
from .database import db_manager
# Create MCP server - Squid Catchers AI Assistant
mcp = fastmcp.FastMCP("Squber - Squid Fishing AI Assistant")


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




# ============================================================================
# FUTURES MARKET TOOLS
# ============================================================================

@mcp.tool()
async def futures_contract_explorer(delivery_month: Optional[str] = None, port_code: Optional[str] = None) -> str:
    """Browse available futures contracts and specifications.

    Args:
        delivery_month: Filter by delivery month (e.g., "2025-03" or "ALL")
        port_code: Filter by delivery port code (e.g., "MNT")

    Returns:
        JSON formatted list of available contracts with specifications
    """
    try:
        # Build query filters
        where_clauses = ["fc.status = 'active'"]

        if delivery_month and delivery_month.upper() != "ALL":
            where_clauses.append(f"fc.delivery_month = '{delivery_month}'")

        if port_code:
            where_clauses.append("p.port_code = :port_code")

        where_clause = " AND ".join(where_clauses)

        query = f"""
        SELECT fc.symbol, fc.contract_type, fc.delivery_month, fc.expiry_date,
               fc.contract_size_tons, fc.grade, fc.settlement_type,
               p.port_name, p.port_code,
               fp.settle_price as current_price,
               fp.volume as daily_volume,
               fp.open_interest
        FROM futures_contracts fc
        LEFT JOIN ports p ON fc.delivery_port_id = p.port_id
        LEFT JOIN futures_prices fp ON fc.contract_id = fp.contract_id
            AND fp.trade_date = (SELECT MAX(trade_date) FROM futures_prices WHERE contract_id = fc.contract_id)
        WHERE {where_clause}
        ORDER BY fc.expiry_date, fc.symbol
        """

        if port_code:
            query = query.replace(":port_code", f"'{port_code}'")
        result = await db_manager.execute_query(query)

        contracts = []
        for row in result["rows"]:
            contract = {
                "symbol": row["symbol"],
                "contract_type": row["contract_type"],
                "delivery_month": row["delivery_month"],
                "expiry_date": row["expiry_date"],
                "contract_size_tons": row["contract_size_tons"],
                "grade": row["grade"],
                "settlement_type": row["settlement_type"],
                "delivery_port": {
                    "name": row["port_name"],
                    "code": row["port_code"]
                } if row["port_name"] else None,
                "current_price": f"${row['current_price']:.3f}/lb" if row["current_price"] else "No recent trading",
                "daily_volume": row["daily_volume"] or 0,
                "open_interest": row["open_interest"] or 0
            }
            contracts.append(contract)

        response = {
            "total_contracts": len(contracts),
            "filters_applied": {
                "delivery_month": delivery_month,
                "port_code": port_code
            },
            "available_contracts": contracts,
            "market_summary": f"Found {len(contracts)} active futures contracts"
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "delivery_month": delivery_month,
            "port_code": port_code
        })


@mcp.tool()
async def futures_market_data(contract_symbol: str, days: int = 30) -> str:
    """Get futures price data and market analysis for a specific contract.

    Args:
        contract_symbol: Contract symbol (e.g., "SQ-MAR25-MNT" or "SQ-MAR25-CASH")
        days: Number of days of price history to analyze (default: 30)

    Returns:
        JSON formatted price data with technical analysis
    """
    try:
        # Get contract info
        contract_query = """
        SELECT fc.*, p.port_name, p.port_code
        FROM futures_contracts fc
        LEFT JOIN ports p ON fc.delivery_port_id = p.port_id
        WHERE fc.symbol = :symbol
        """

        contract_result = await db_manager.execute_query(contract_query, params={"symbol": contract_symbol})

        if not contract_result["rows"]:
            return json.dumps({"error": f"Contract {contract_symbol} not found"})

        contract = contract_result["rows"][0]

        # Get recent price history
        price_query = """
        SELECT trade_date, open_price, high_price, low_price, close_price,
               settle_price, volume, open_interest
        FROM futures_prices fp
        WHERE fp.contract_id = :contract_id
            AND fp.trade_date >= date('now', '-' || :days || ' days')
        ORDER BY fp.trade_date DESC
        """

        price_result = await db_manager.execute_query(
            price_query,
            params={"contract_id": contract["contract_id"], "days": days}
        )

        if not price_result["rows"]:
            return json.dumps({"error": "No price data available for this contract"})

        prices = price_result["rows"]
        latest = prices[0]

        # Calculate basic statistics
        settle_prices = [p["settle_price"] for p in prices if p["settle_price"]]
        if len(settle_prices) > 1:
            price_change = settle_prices[0] - settle_prices[1]
            pct_change = (price_change / settle_prices[1]) * 100

            high_price = max(settle_prices)
            low_price = min(settle_prices)
            avg_price = sum(settle_prices) / len(settle_prices)

            # Simple volatility calculation
            price_changes = [(settle_prices[i] - settle_prices[i+1]) / settle_prices[i+1]
                           for i in range(len(settle_prices)-1)]
            volatility = (sum([(pc - sum(price_changes)/len(price_changes))**2
                             for pc in price_changes]) / len(price_changes))**0.5 * 100
        else:
            price_change = 0
            pct_change = 0
            high_price = low_price = avg_price = settle_prices[0]
            volatility = 0

        # Days to expiry
        expiry_date = datetime.strptime(contract["expiry_date"], "%Y-%m-%d").date()
        days_to_expiry = (expiry_date - date.today()).days

        response = {
            "contract_info": {
                "symbol": contract["symbol"],
                "delivery_month": contract["delivery_month"],
                "expiry_date": contract["expiry_date"],
                "days_to_expiry": days_to_expiry,
                "contract_size_tons": contract["contract_size_tons"],
                "settlement_type": contract["settlement_type"],
                "delivery_port": f"{contract['port_name']} ({contract['port_code']})" if contract["port_name"] else "Cash settled"
            },
            "current_market": {
                "latest_price": f"${latest['settle_price']:.3f}/lb",
                "daily_change": f"${price_change:+.3f} ({pct_change:+.1f}%)",
                "daily_volume": latest["volume"],
                "open_interest": latest["open_interest"],
                "last_updated": latest["trade_date"]
            },
            "price_statistics": {
                f"{days}_day_high": f"${high_price:.3f}/lb",
                f"{days}_day_low": f"${low_price:.3f}/lb",
                f"{days}_day_average": f"${avg_price:.3f}/lb",
                f"{days}_day_volatility": f"{volatility:.1f}%"
            },
            "price_history": [
                {
                    "date": p["trade_date"],
                    "settle": f"${p['settle_price']:.3f}/lb",
                    "volume": p["volume"],
                    "open_interest": p["open_interest"]
                } for p in prices
            ]
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "contract_symbol": contract_symbol,
            "days": days
        })


@mcp.tool()
async def futures_position_tracker(vessel_name: str) -> str:
    """Track current futures positions and P&L for a vessel.

    Args:
        vessel_name: Name of the vessel to track positions for

    Returns:
        JSON formatted position summary with P&L analysis
    """
    try:
        # Get vessel info
        vessel_query = "SELECT vessel_id, vessel_name FROM vessels WHERE vessel_name = :vessel_name"
        vessel_result = await db_manager.execute_query(vessel_query, params={"vessel_name": vessel_name})

        if not vessel_result["rows"]:
            return json.dumps({"error": f"Vessel '{vessel_name}' not found"})

        vessel = vessel_result["rows"][0]

        # Get open positions with current prices
        positions_query = """
        SELECT fp.position_id, fp.position_type, fp.quantity, fp.entry_price,
               fp.entry_date, fp.margin_requirement, fp.unrealized_pnl, fp.notes,
               fc.symbol, fc.expiry_date, fc.contract_size_tons,
               prices.settle_price as current_price
        FROM futures_positions fp
        JOIN futures_contracts fc ON fp.contract_id = fc.contract_id
        LEFT JOIN (
            SELECT contract_id, settle_price,
                   ROW_NUMBER() OVER (PARTITION BY contract_id ORDER BY trade_date DESC) as rn
            FROM futures_prices
        ) prices ON fc.contract_id = prices.contract_id AND prices.rn = 1
        WHERE fp.vessel_id = :vessel_id AND fp.status = 'open'
        ORDER BY fp.entry_date DESC
        """

        positions_result = await db_manager.execute_query(
            positions_query,
            params={"vessel_id": vessel["vessel_id"]}
        )

        positions = []
        total_unrealized_pnl = 0
        total_margin = 0

        for pos in positions_result["rows"]:
            # Recalculate current P&L
            if pos["current_price"]:
                notional_per_contract = pos["current_price"] * pos["contract_size_tons"] * 2000  # price * tons * lbs
                total_notional = notional_per_contract * pos["quantity"]

                if pos["position_type"] == "long":
                    current_pnl = (pos["current_price"] - pos["entry_price"]) * pos["contract_size_tons"] * 2000 * pos["quantity"]
                else:  # short
                    current_pnl = (pos["entry_price"] - pos["current_price"]) * pos["contract_size_tons"] * 2000 * pos["quantity"]

                total_unrealized_pnl += current_pnl
                total_margin += pos["margin_requirement"] or 0

                position_info = {
                    "position_id": pos["position_id"],
                    "contract": pos["symbol"],
                    "position_type": pos["position_type"],
                    "quantity": pos["quantity"],
                    "entry_price": f"${pos['entry_price']:.3f}/lb",
                    "current_price": f"${pos['current_price']:.3f}/lb",
                    "entry_date": pos["entry_date"],
                    "unrealized_pnl": f"${current_pnl:,.2f}",
                    "margin_requirement": f"${pos['margin_requirement']:,.2f}" if pos["margin_requirement"] else "N/A",
                    "expiry_date": pos["expiry_date"],
                    "notes": pos["notes"]
                }
                positions.append(position_info)

        # Portfolio summary
        margin_utilization = (total_margin / (total_margin + 50000)) * 100 if total_margin > 0 else 0  # Assume $50k available

        response = {
            "vessel_info": {
                "vessel_name": vessel["vessel_name"],
                "vessel_id": vessel["vessel_id"]
            },
            "portfolio_summary": {
                "total_positions": len(positions),
                "total_unrealized_pnl": f"${total_unrealized_pnl:,.2f}",
                "total_margin_requirement": f"${total_margin:,.2f}",
                "margin_utilization": f"{margin_utilization:.1f}%",
                "status": "Healthy" if margin_utilization < 80 else "Margin Call Risk"
            },
            "open_positions": positions,
            "risk_analysis": {
                "largest_position": max([abs(float(p["unrealized_pnl"].replace("$", "").replace(",", "")))
                                       for p in positions], default=0),
                "pnl_trend": "Positive" if total_unrealized_pnl > 0 else "Negative" if total_unrealized_pnl < 0 else "Neutral"
            }
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "vessel_name": vessel_name
        })


@mcp.tool()
async def futures_hedge_advisor(vessel_name: str, expected_catch_tons: float, target_month: str) -> str:
    """Provide hedging recommendations for planned fishing trips.

    Args:
        vessel_name: Name of the vessel planning the trip
        expected_catch_tons: Anticipated catch size in tons
        target_month: Expected landing month (e.g., "2025-03")

    Returns:
        JSON formatted hedging strategy recommendations
    """
    try:
        # Get vessel info
        vessel_query = "SELECT vessel_id, vessel_name, capacity_tons FROM vessels WHERE vessel_name = :vessel_name"
        vessel_result = await db_manager.execute_query(vessel_query, params={"vessel_name": vessel_name})

        if not vessel_result["rows"]:
            return json.dumps({"error": f"Vessel '{vessel_name}' not found"})

        vessel = vessel_result["rows"][0]

        # Validate catch size
        if expected_catch_tons > vessel["capacity_tons"]:
            return json.dumps({
                "error": f"Expected catch ({expected_catch_tons} tons) exceeds vessel capacity ({vessel['capacity_tons']} tons)"
            })

        # Get available contracts for target month
        contracts_query = """
        SELECT fc.symbol, fc.contract_id, fc.contract_size_tons, fc.settlement_type,
               p.port_name, p.port_code,
               fp.settle_price as current_price
        FROM futures_contracts fc
        LEFT JOIN ports p ON fc.delivery_port_id = p.port_id
        LEFT JOIN futures_prices fp ON fc.contract_id = fp.contract_id
            AND fp.trade_date = (SELECT MAX(trade_date) FROM futures_prices WHERE contract_id = fc.contract_id)
        WHERE fc.delivery_month = :target_month
            AND fc.status = 'active'
            AND fp.settle_price IS NOT NULL
        ORDER BY fp.settle_price DESC
        """

        contracts_result = await db_manager.execute_query(
            contracts_query,
            params={"target_month": target_month}
        )

        if not contracts_result["rows"]:
            return json.dumps({
                "error": f"No active futures contracts found for {target_month}"
            })

        # Get current spot prices for comparison
        spot_query = """
        SELECT AVG(price_per_lb) as avg_spot_price
        FROM market_prices
        WHERE price_date >= date('now', '-7 days')
            AND grade = 'A'
        """
        spot_result = await db_manager.execute_query(spot_query)
        avg_spot_price = spot_result["rows"][0]["avg_spot_price"] if spot_result["rows"] else 2.50

        # Analyze contracts and recommend hedging strategy
        best_contract = max(contracts_result["rows"], key=lambda x: x["current_price"])

        # Calculate hedging scenarios
        total_catch_lbs = expected_catch_tons * 2000
        hedge_ratios = [0.5, 0.75, 0.9]  # 50%, 75%, 90% hedge ratios

        hedging_scenarios = []
        for ratio in hedge_ratios:
            hedge_amount_lbs = total_catch_lbs * ratio
            contracts_needed = hedge_amount_lbs / (best_contract["contract_size_tons"] * 2000)

            # Revenue calculations
            hedged_revenue = hedge_amount_lbs * best_contract["current_price"]
            unhedged_lbs = total_catch_lbs - hedge_amount_lbs

            # Margin requirement (assume 10% of notional)
            notional_value = hedge_amount_lbs * best_contract["current_price"]
            margin_required = notional_value * 0.10

            scenario = {
                "hedge_ratio": f"{ratio*100:.0f}%",
                "hedge_amount_tons": hedge_amount_lbs / 2000,
                "contracts_needed": round(contracts_needed, 2),
                "guaranteed_revenue": f"${hedged_revenue:,.0f}",
                "unhedged_exposure_tons": unhedged_lbs / 2000,
                "margin_requirement": f"${margin_required:,.0f}",
                "hedge_price": f"${best_contract['current_price']:.3f}/lb"
            }
            hedging_scenarios.append(scenario)

        # Risk analysis
        price_scenarios = [
            {"market_price": 2.00, "scenario": "Price Crash"},
            {"market_price": avg_spot_price, "scenario": "Current Market"},
            {"market_price": 3.50, "scenario": "Price Surge"}
        ]

        risk_analysis = []
        for price_scenario in price_scenarios:
            unhedged_revenue = total_catch_lbs * price_scenario["market_price"]

            # Best hedge scenario (75%)
            best_hedge = hedging_scenarios[1]  # 75% hedge
            hedged_portion = total_catch_lbs * 0.75 * best_contract["current_price"]
            unhedged_portion = total_catch_lbs * 0.25 * price_scenario["market_price"]
            hedged_total = hedged_portion + unhedged_portion

            risk_analysis.append({
                "scenario": price_scenario["scenario"],
                "market_price": f"${price_scenario['market_price']:.2f}/lb",
                "unhedged_revenue": f"${unhedged_revenue:,.0f}",
                "hedged_revenue_75pct": f"${hedged_total:,.0f}",
                "protection_value": f"${hedged_total - unhedged_revenue:+,.0f}"
            })

        response = {
            "vessel_info": {
                "vessel_name": vessel["vessel_name"],
                "expected_catch_tons": expected_catch_tons,
                "target_month": target_month
            },
            "market_analysis": {
                "current_spot_average": f"${avg_spot_price:.3f}/lb",
                "best_futures_price": f"${best_contract['current_price']:.3f}/lb",
                "futures_premium": f"${best_contract['current_price'] - avg_spot_price:+.3f}/lb",
                "recommended_contract": best_contract["symbol"]
            },
            "hedging_scenarios": hedging_scenarios,
            "recommended_strategy": {
                "hedge_ratio": "75%",
                "reasoning": "Optimal balance of price protection and upside participation",
                "action": f"Sell {hedging_scenarios[1]['contracts_needed']} contracts of {best_contract['symbol']}",
                "margin_needed": hedging_scenarios[1]["margin_requirement"]
            },
            "risk_analysis": risk_analysis,
            "next_steps": [
                "Contact futures broker to establish margin account",
                "Monitor basis convergence as delivery approaches",
                "Consider adjusting hedge ratio based on fishing success",
                "Plan delivery logistics if using physical settlement"
            ]
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "vessel_name": vessel_name,
            "expected_catch_tons": expected_catch_tons,
            "target_month": target_month
        })


@mcp.tool()
async def futures_basis_analysis(port_code: str, contract_symbol: str) -> str:
    """Analyze basis (futures - spot price difference) for arbitrage opportunities.

    Args:
        port_code: Local port code for spot prices (e.g., "MNT")
        contract_symbol: Futures contract symbol (e.g., "SQ-MAR25-MNT")

    Returns:
        JSON formatted basis analysis with arbitrage insights
    """
    try:
        # Get port info
        port_query = "SELECT port_id, port_name, port_code FROM ports WHERE port_code = :port_code"
        port_result = await db_manager.execute_query(port_query, params={"port_code": port_code})

        if not port_result["rows"]:
            return json.dumps({"error": f"Port '{port_code}' not found"})

        port = port_result["rows"][0]

        # Get contract info and current futures price
        contract_query = """
        SELECT fc.*, fp.settle_price as futures_price, fp.trade_date as futures_date
        FROM futures_contracts fc
        LEFT JOIN futures_prices fp ON fc.contract_id = fp.contract_id
            AND fp.trade_date = (SELECT MAX(trade_date) FROM futures_prices WHERE contract_id = fc.contract_id)
        WHERE fc.symbol = :symbol
        """

        contract_result = await db_manager.execute_query(contract_query, params={"symbol": contract_symbol})

        if not contract_result["rows"]:
            return json.dumps({"error": f"Contract '{contract_symbol}' not found"})

        contract = contract_result["rows"][0]

        # Get recent spot prices at the port
        spot_query = """
        SELECT price_per_lb, price_date
        FROM market_prices mp
        JOIN ports p ON mp.port_id = p.port_id
        WHERE p.port_code = :port_code
            AND mp.grade = 'A'
            AND mp.price_date >= date('now', '-30 days')
        ORDER BY mp.price_date DESC
        LIMIT 1
        """

        spot_result = await db_manager.execute_query(spot_query, params={"port_code": port_code})

        if not spot_result["rows"]:
            return json.dumps({"error": f"No recent spot price data for port {port_code}"})

        current_spot = spot_result["rows"][0]

        # Calculate basis
        basis = contract["futures_price"] - current_spot["price_per_lb"]
        basis_percentage = (basis / current_spot["price_per_lb"]) * 100

        # Get historical basis data
        historical_query = """
        SELECT fp.trade_date, fp.settle_price as futures_price,
               mp.price_per_lb as spot_price,
               (fp.settle_price - mp.price_per_lb) as basis
        FROM futures_prices fp
        JOIN futures_contracts fc ON fp.contract_id = fc.contract_id
        JOIN market_prices mp ON fp.trade_date = mp.price_date
        JOIN ports p ON mp.port_id = p.port_id
        WHERE fc.symbol = :symbol
            AND p.port_code = :port_code
            AND mp.grade = 'A'
            AND fp.trade_date >= date('now', '-30 days')
        ORDER BY fp.trade_date DESC
        """

        historical_result = await db_manager.execute_query(
            historical_query,
            params={"symbol": contract_symbol, "port_code": port_code}
        )

        # Calculate basis statistics
        if historical_result["rows"]:
            basis_values = [row["basis"] for row in historical_result["rows"]]
            avg_basis = sum(basis_values) / len(basis_values)
            max_basis = max(basis_values)
            min_basis = min(basis_values)
            basis_volatility = (sum([(b - avg_basis)**2 for b in basis_values]) / len(basis_values))**0.5
        else:
            avg_basis = basis
            max_basis = min_basis = basis
            basis_volatility = 0

        # Days to expiry
        expiry_date = datetime.strptime(contract["expiry_date"], "%Y-%m-%d").date()
        days_to_expiry = (expiry_date - date.today()).days

        # Expected basis convergence
        expected_basis_at_expiry = 0.02  # Typical convergence to small premium
        expected_convergence = basis - expected_basis_at_expiry

        # Arbitrage analysis
        arbitrage_opportunities = []

        if basis > avg_basis + basis_volatility:
            arbitrage_opportunities.append({
                "type": "Sell Futures, Buy Spot",
                "reasoning": "Futures appears overpriced relative to historical basis",
                "expected_profit": f"${expected_convergence:.3f}/lb",
                "risk_level": "Medium"
            })

        if basis < avg_basis - basis_volatility:
            arbitrage_opportunities.append({
                "type": "Buy Futures, Sell Spot",
                "reasoning": "Futures appears underpriced relative to historical basis",
                "expected_profit": f"${-expected_convergence:.3f}/lb",
                "risk_level": "Medium"
            })

        if abs(basis) < 0.01 and days_to_expiry > 30:
            arbitrage_opportunities.append({
                "type": "Calendar Spread",
                "reasoning": "Very tight basis suggests look at other contract months",
                "expected_profit": "Variable",
                "risk_level": "Low"
            })

        response = {
            "analysis_date": datetime.now().isoformat(),
            "market_data": {
                "port": f"{port['port_name']} ({port['port_code']})",
                "contract": contract_symbol,
                "spot_price": f"${current_spot['price_per_lb']:.3f}/lb",
                "futures_price": f"${contract['futures_price']:.3f}/lb",
                "current_basis": f"${basis:+.3f}/lb ({basis_percentage:+.1f}%)"
            },
            "historical_basis": {
                "30_day_average": f"${avg_basis:.3f}/lb",
                "30_day_high": f"${max_basis:.3f}/lb",
                "30_day_low": f"${min_basis:.3f}/lb",
                "volatility": f"${basis_volatility:.3f}/lb"
            },
            "convergence_analysis": {
                "days_to_expiry": days_to_expiry,
                "expected_basis_at_expiry": f"${expected_basis_at_expiry:.3f}/lb",
                "expected_convergence": f"${expected_convergence:.3f}/lb",
                "convergence_rate": f"${expected_convergence/max(days_to_expiry, 1):.4f}/lb per day"
            },
            "arbitrage_opportunities": arbitrage_opportunities if arbitrage_opportunities else ["No clear arbitrage opportunities identified"],
            "risk_factors": [
                "Basis can be volatile near expiry",
                "Storage and transportation costs affect arbitrage",
                "Delivery logistics may impact physical settlement",
                "Market liquidity varies by contract"
            ],
            "historical_data": [
                {
                    "date": row["trade_date"],
                    "futures": f"${row['futures_price']:.3f}/lb",
                    "spot": f"${row['spot_price']:.3f}/lb",
                    "basis": f"${row['basis']:+.3f}/lb"
                } for row in historical_result["rows"][:10]  # Last 10 days
            ]
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "port_code": port_code,
            "contract_symbol": contract_symbol
        })


@mcp.resource("config://settings")
def get_settings() -> dict[str, Any]:
    """Get application settings."""
    return {
        "app_name": "squber",
        "version": "0.1.0",
        "environment": os.getenv("SQUBER_ENV", "development"),
        "database": "SQLite with squid fishing maritime data",
        "description": "AI Assistant for Squid Fishers - Market Intelligence & Trip Planning"
    }


def main(transport: str = "stdio") -> None:
    """Run the FastMCP server."""
    if transport == "http":
        # Run with Streamable HTTP transport (recommended for web access)
        host = os.getenv("SQUBER_HOST", "0.0.0.0")
        port = int(os.getenv("SQUBER_PORT", 8000))

        print(f"🦑 Starting Squber with Streamable HTTP on http://{host}:{port}")
        print(f"🌍 Environment: {os.getenv('SQUBER_ENV', 'development')}")
        print(f"🌐 MCP Endpoint: http://{host}:{port}/ (single endpoint)")
        print(f"📡 Transport: Streamable HTTP (MCP 2024-11-05 spec)")

        mcp.run(transport="http", host=host, port=port)
    else:
        # Default STDIO transport
        mcp.run()
