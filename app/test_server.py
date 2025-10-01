#!/usr/bin/env python3
"""Test script for the Squid Fishing AI Assistant."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_squid_fishing_assistant():
    """Test the squid fishing AI assistant tools."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "squber"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("🦑 SQUID CATCHERS AI ASSISTANT - TOOLS")
            print("="*60)
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            print("\n" + "="*60)
            print("📊 Testing squber_howto - Maritime Database Schema")
            print("="*60)

            # Test squber_howto tool for maritime schema
            result = await session.call_tool("squber_howto", {})
            schema_data = json.loads(result.content[0].text)
            print(f"Maritime database: {schema_data['database_info']['description']}")
            print(f"Tables: {schema_data['database_info']['total_tables']}")
            for table in schema_data['database_info']['tables']:
                print(f"  - {table}")

            print(f"\nKey captain questions addressed:")
            for question in schema_data['key_questions']:
                print(f"  • {question}")

            print("\n" + "="*60)
            print("🎯 Testing get_market_report - Market Intelligence")
            print("="*60)

            # Test market report
            result = await session.call_tool("get_market_report", {"days": 7, "port_codes": "MNT,MOR,SB"})
            market_data = json.loads(result.content[0].text)

            print(f"Market Report Generated: {market_data['report_date']}")
            print(f"Analysis Period: {market_data['analysis_period_days']} days")
            print(f"{market_data['summary']}")

            if market_data.get('recommendations'):
                print("\nRecommendations:")
                for rec in market_data['recommendations']:
                    print(f"  • {rec}")

            if market_data.get('market_prices'):
                print(f"\nPrice Data Points: {len(market_data['market_prices'])}")
                for price in market_data['market_prices'][:3]:  # Show top 3
                    print(f"  {price['port_name']} Grade {price['grade']}: ${price['avg_price']:.2f}/lb")

            print("\n" + "="*60)
            print("🚢 Testing trip_advisor - Trip Planning")
            print("="*60)

            # Test trip advisor
            result = await session.call_tool("trip_advisor", {
                "vessel_name": "PACIFIC HUNTER",
                "target_port": "MNT"
            })
            trip_data = json.loads(result.content[0].text)

            print(f"Trip advice generated for: {trip_data.get('vessel_query', 'General')}")
            print(f"Target port: {trip_data.get('target_port', 'Any')}")

            if trip_data.get('recommendations'):
                print("\nTrip Recommendations:")
                for rec in trip_data['recommendations']:
                    print(f"  {rec}")

            print("\n" + "="*60)
            print("🗃️ Testing query_data - Maritime Queries")
            print("="*60)

            # Test fishing-specific queries
            fishing_queries = [
                "SELECT COUNT(*) as total_ports FROM ports",
                "SELECT port_name, market_tier, processing_capacity FROM ports WHERE state = 'CA' ORDER BY processing_capacity DESC LIMIT 5",
                "SELECT vessel_name, vessel_type, capacity_tons FROM vessels ORDER BY capacity_tons DESC LIMIT 3",
                "SELECT regulation_type, description FROM fishing_regulations WHERE is_active = 1 AND species = 'Market Squid'"
            ]

            for i, query in enumerate(fishing_queries, 1):
                print(f"\nMaritime Query {i}: {query}")
                result = await session.call_tool("query_data", {"query": query})
                query_result = json.loads(result.content[0].text)

                if "success" in query_result and query_result["success"]:
                    print(f"  ✅ Returned {query_result['row_count']} rows")
                    if query_result['rows']:
                        print("  📋 Sample results:")
                        for row in query_result['rows'][:2]:
                            print(f"    {row}")
                else:
                    print(f"  ❌ Error: {query_result.get('error', 'Unknown error')}")

            print("\n" + "="*60)
            print("🔒 Testing Security - Non-SELECT Query")
            print("="*60)

            # Test security with non-SELECT query
            bad_query = "INSERT INTO ports (port_name) VALUES ('Fake Port')"
            result = await session.call_tool("query_data", {"query": bad_query})
            security_result = json.loads(result.content[0].text)
            print(f"✅ Security check: {security_result.get('error', 'No error')}")

            print("\n" + "="*60)
            print("📚 Resources Available")
            print("="*60)

            # List available resources
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.name}")

            print("\n🎉 Squid Fishing AI Assistant testing complete!")
            print("Ready to help captains answer:")
            print("  1. When should I leave port?")
            print("  2. When should I return?")
            print("  3. Which port should I land in?")


if __name__ == "__main__":
    asyncio.run(test_squid_fishing_assistant())