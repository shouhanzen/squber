"""Generate realistic futures market data for squid trading."""

import asyncio
import random
from datetime import datetime, timedelta, date
from sqlalchemy import text
from .database import db_manager


async def generate_futures_data():
    """Generate sample futures contracts and price data."""
    async with db_manager.async_session() as session:

        # Clear existing futures data
        await session.execute(text("DELETE FROM futures_settlements"))
        await session.execute(text("DELETE FROM futures_positions"))
        await session.execute(text("DELETE FROM futures_prices"))
        await session.execute(text("DELETE FROM futures_contracts"))

        # Create futures contracts (next 6 months)
        contracts_data = []

        # Monthly contracts for next 6 months
        base_date = datetime.now().date()
        for i in range(6):
            contract_month = base_date + timedelta(days=30 * (i + 1))
            month_str = contract_month.strftime("%b").upper()
            year_str = contract_month.strftime("%y")

            # Physical delivery contracts
            for port_id, port_name in [(1, "Monterey"), (2, "Morro Bay"), (3, "Santa Barbara")]:
                symbol = f"SQ-{month_str}{year_str}-{port_name[:3].upper()}"
                expiry = contract_month.replace(day=15)  # 15th of delivery month

                contracts_data.append({
                    'symbol': symbol,
                    'contract_type': 'monthly',
                    'delivery_month': contract_month.strftime("%Y-%m"),
                    'expiry_date': expiry,
                    'contract_size_tons': 50,
                    'delivery_port_id': port_id,
                    'grade': 'A',
                    'tick_size': 0.01,
                    'created_date': base_date,
                    'status': 'active',
                    'settlement_type': 'physical'
                })

        # Cash-settled contracts (broader market)
        for i in range(6):
            contract_month = base_date + timedelta(days=30 * (i + 1))
            month_str = contract_month.strftime("%b").upper()
            year_str = contract_month.strftime("%y")

            symbol = f"SQ-{month_str}{year_str}-CASH"
            expiry = contract_month.replace(day=28)  # Last trading day

            contracts_data.append({
                'symbol': symbol,
                'contract_type': 'monthly',
                'delivery_month': contract_month.strftime("%Y-%m"),
                'expiry_date': expiry,
                'contract_size_tons': 50,
                'delivery_port_id': None,  # Cash settled
                'grade': 'A',
                'tick_size': 0.01,
                'created_date': base_date,
                'status': 'active',
                'settlement_type': 'cash'
            })

        # Quarterly contracts
        quarters = [
            ("Q1", "2025-03-31"), ("Q2", "2025-06-30"),
            ("Q3", "2025-09-30"), ("Q4", "2025-12-31")
        ]

        for q_name, q_end in quarters:
            if datetime.strptime(q_end, "%Y-%m-%d").date() > base_date:
                symbol = f"SQ-{q_name}-25"
                expiry = datetime.strptime(q_end, "%Y-%m-%d").date()

                contracts_data.append({
                    'symbol': symbol,
                    'contract_type': 'quarterly',
                    'delivery_month': q_name,
                    'expiry_date': expiry,
                    'contract_size_tons': 100,  # Larger quarterly contracts
                    'delivery_port_id': None,   # Cash settled
                    'grade': 'A',
                    'tick_size': 0.01,
                    'created_date': base_date,
                    'status': 'active',
                    'settlement_type': 'cash'
                })

        # Insert contracts
        for contract in contracts_data:
            await session.execute(text("""
                INSERT INTO futures_contracts
                (symbol, contract_type, delivery_month, expiry_date, contract_size_tons,
                 delivery_port_id, grade, tick_size, created_date, status, settlement_type)
                VALUES (:symbol, :contract_type, :delivery_month, :expiry_date, :contract_size_tons,
                        :delivery_port_id, :grade, :tick_size, :created_date, :status, :settlement_type)
            """), contract)

        await session.commit()

        # Get contract IDs for price generation
        result = await session.execute(text("SELECT contract_id, symbol FROM futures_contracts"))
        contracts = result.fetchall()

        # Generate price history (90 days)
        price_data = []

        for contract_id, symbol in contracts:
            # Base price varies by time to expiry and market conditions
            if "CASH" in symbol:
                base_price = 2.75  # Cash settled slightly lower
            elif "Q1" in symbol or "Q2" in symbol:
                base_price = 2.85  # Peak season premium
            else:
                base_price = 2.65  # Off season

            # Generate 90 days of price history
            current_price = base_price + random.uniform(-0.15, 0.15)

            for days_back in range(90, 0, -1):
                trade_date = base_date - timedelta(days=days_back)

                # Price walks with mean reversion
                price_change = random.gauss(0, 0.03)  # 3 cent daily volatility
                mean_reversion = (base_price - current_price) * 0.1
                current_price += price_change + mean_reversion

                # Ensure reasonable bounds
                current_price = max(1.50, min(4.00, current_price))

                # Generate OHLC data
                open_price = current_price
                volatility = 0.02  # 2 cent intraday range
                high_price = open_price + random.uniform(0, volatility)
                low_price = open_price - random.uniform(0, volatility)
                close_price = open_price + random.uniform(-volatility/2, volatility/2)
                settle_price = close_price + random.uniform(-0.005, 0.005)

                # Volume and open interest (higher for near months)
                days_to_expiry = (datetime.strptime(str(base_date), "%Y-%m-%d") -
                                 datetime.strptime(str(trade_date), "%Y-%m-%d")).days
                volume_factor = max(10, 200 - days_to_expiry)
                volume = random.randint(volume_factor//2, volume_factor)
                open_interest = random.randint(500, 2000)

                current_price = settle_price

                price_data.append({
                    'contract_id': contract_id,
                    'trade_date': trade_date,
                    'open_price': round(open_price, 3),
                    'high_price': round(high_price, 3),
                    'low_price': round(low_price, 3),
                    'close_price': round(close_price, 3),
                    'settle_price': round(settle_price, 3),
                    'volume': volume,
                    'open_interest': open_interest
                })

        # Insert price data in batches
        batch_size = 100
        for i in range(0, len(price_data), batch_size):
            batch = price_data[i:i + batch_size]
            for price in batch:
                await session.execute(text("""
                    INSERT INTO futures_prices
                    (contract_id, trade_date, open_price, high_price, low_price,
                     close_price, settle_price, volume, open_interest)
                    VALUES (:contract_id, :trade_date, :open_price, :high_price, :low_price,
                            :close_price, :settle_price, :volume, :open_interest)
                """), price)

            await session.commit()

        # Generate some sample positions for vessels
        vessel_result = await session.execute(text("SELECT vessel_id, vessel_name FROM vessels LIMIT 3"))
        vessels = vessel_result.fetchall()

        position_data = []
        for vessel_id, vessel_name in vessels:
            # Each vessel has 1-3 positions
            num_positions = random.randint(1, 3)

            for _ in range(num_positions):
                # Pick a random contract
                contract_id = random.choice([c[0] for c in contracts])

                # Position details
                position_type = random.choice(['long', 'short'])
                quantity = random.randint(1, 5)  # 1-5 contracts
                entry_price = 2.70 + random.uniform(-0.20, 0.20)
                entry_date = base_date - timedelta(days=random.randint(1, 30))

                # Calculate margin (10% of notional value)
                notional_value = entry_price * 50 * 2000 * quantity  # price * tons * lbs * contracts
                margin_requirement = notional_value * 0.10

                # Calculate current P&L (simplified)
                current_settle = 2.75  # Current market price
                if position_type == 'long':
                    unrealized_pnl = (current_settle - entry_price) * 50 * 2000 * quantity
                else:
                    unrealized_pnl = (entry_price - current_settle) * 50 * 2000 * quantity

                position_data.append({
                    'vessel_id': vessel_id,
                    'contract_id': contract_id,
                    'position_type': position_type,
                    'quantity': quantity,
                    'entry_price': round(entry_price, 3),
                    'entry_date': entry_date,
                    'status': 'open',
                    'margin_requirement': round(margin_requirement, 2),
                    'unrealized_pnl': round(unrealized_pnl, 2),
                    'notes': f"Sample position for {vessel_name}"
                })

        # Insert positions
        for position in position_data:
            await session.execute(text("""
                INSERT INTO futures_positions
                (vessel_id, contract_id, position_type, quantity, entry_price, entry_date,
                 status, margin_requirement, unrealized_pnl, notes)
                VALUES (:vessel_id, :contract_id, :position_type, :quantity, :entry_price, :entry_date,
                        :status, :margin_requirement, :unrealized_pnl, :notes)
            """), position)

        await session.commit()

        print(f"Generated {len(contracts_data)} futures contracts")
        print(f"Generated {len(price_data)} price records")
        print(f"Generated {len(position_data)} sample positions")
        print("Futures market data generated successfully!")


if __name__ == "__main__":
    asyncio.run(generate_futures_data())