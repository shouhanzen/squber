"""Seed the database with sample data."""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from squber.database import db_manager


async def create_tables():
    """Create sample tables."""
    async with db_manager.async_session() as session:
        # Customers table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                city TEXT,
                state TEXT,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Products table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock_quantity INTEGER DEFAULT 0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Orders table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10,2),
                status TEXT DEFAULT 'pending',
                shipping_address TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """))

        # Order items table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """))

        await session.commit()


async def seed_customers():
    """Insert sample customer data."""
    customers = [
        ("John", "Doe", "john.doe@email.com", "+1-555-0101", "New York", "NY", "USA"),
        ("Jane", "Smith", "jane.smith@email.com", "+1-555-0102", "Los Angeles", "CA", "USA"),
        ("Bob", "Johnson", "bob.johnson@email.com", "+1-555-0103", "Chicago", "IL", "USA"),
        ("Alice", "Brown", "alice.brown@email.com", "+1-555-0104", "Houston", "TX", "USA"),
        ("Charlie", "Wilson", "charlie.wilson@email.com", "+1-555-0105", "Phoenix", "AZ", "USA"),
        ("Diana", "Davis", "diana.davis@email.com", "+1-555-0106", "Philadelphia", "PA", "USA"),
        ("Eve", "Miller", "eve.miller@email.com", "+1-555-0107", "San Antonio", "TX", "USA"),
        ("Frank", "Garcia", "frank.garcia@email.com", "+1-555-0108", "San Diego", "CA", "USA"),
        ("Grace", "Rodriguez", "grace.rodriguez@email.com", "+1-555-0109", "Dallas", "TX", "USA"),
        ("Henry", "Martinez", "henry.martinez@email.com", "+1-555-0110", "San Jose", "CA", "USA"),
    ]

    async with db_manager.async_session() as session:
        for customer in customers:
            await session.execute(text("""
                INSERT OR IGNORE INTO customers (first_name, last_name, email, phone, city, state, country)
                VALUES (:first_name, :last_name, :email, :phone, :city, :state, :country)
            """), {
                "first_name": customer[0],
                "last_name": customer[1],
                "email": customer[2],
                "phone": customer[3],
                "city": customer[4],
                "state": customer[5],
                "country": customer[6]
            })
        await session.commit()


async def seed_products():
    """Insert sample product data."""
    products = [
        ("Laptop", "Electronics", 999.99, 50, "High-performance laptop for work and gaming"),
        ("Smartphone", "Electronics", 699.99, 100, "Latest smartphone with advanced features"),
        ("Headphones", "Electronics", 199.99, 75, "Noise-canceling wireless headphones"),
        ("Coffee Maker", "Kitchen", 89.99, 30, "Programmable coffee maker with timer"),
        ("Running Shoes", "Sports", 129.99, 60, "Comfortable running shoes for all terrains"),
        ("Backpack", "Fashion", 59.99, 40, "Durable backpack for travel and work"),
        ("Desk Chair", "Furniture", 249.99, 25, "Ergonomic office chair with lumbar support"),
        ("Water Bottle", "Sports", 24.99, 150, "Insulated stainless steel water bottle"),
        ("Notebook", "Office", 12.99, 200, "Premium notebook for writing and sketching"),
        ("Wireless Mouse", "Electronics", 39.99, 80, "Ergonomic wireless mouse with precision tracking"),
    ]

    async with db_manager.async_session() as session:
        for product in products:
            await session.execute(text("""
                INSERT OR IGNORE INTO products (name, category, price, stock_quantity, description)
                VALUES (:name, :category, :price, :stock_quantity, :description)
            """), {
                "name": product[0],
                "category": product[1],
                "price": product[2],
                "stock_quantity": product[3],
                "description": product[4]
            })
        await session.commit()


async def seed_orders():
    """Insert sample order data."""
    import random

    async with db_manager.async_session() as session:
        # Get customer and product IDs
        customer_result = await session.execute(text("SELECT customer_id FROM customers"))
        customer_ids = [row[0] for row in customer_result.fetchall()]

        product_result = await session.execute(text("SELECT product_id, price FROM products"))
        products = [(row[0], row[1]) for row in product_result.fetchall()]

        statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]

        # Create 25 sample orders
        for i in range(25):
            customer_id = random.choice(customer_ids)
            status = random.choice(statuses)
            order_date = datetime.now() - timedelta(days=random.randint(1, 90))

            # Insert order
            result = await session.execute(text("""
                INSERT INTO orders (customer_id, order_date, status, shipping_address)
                VALUES (:customer_id, :order_date, :status, :shipping_address)
            """), {
                "customer_id": customer_id,
                "order_date": order_date,
                "status": status,
                "shipping_address": f"Address {i+1}, City, State 12345"
            })

            order_id = result.lastrowid

            # Add random order items
            num_items = random.randint(1, 4)
            total_amount = 0

            for _ in range(num_items):
                product_id, price = random.choice(products)
                quantity = random.randint(1, 3)
                unit_price = float(price)
                total_amount += unit_price * quantity

                await session.execute(text("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (:order_id, :product_id, :quantity, :unit_price)
                """), {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price
                })

            # Update order total
            await session.execute(text("""
                UPDATE orders SET total_amount = :total_amount WHERE order_id = :order_id
            """), {
                "total_amount": total_amount,
                "order_id": order_id
            })

        await session.commit()


async def seed_database():
    """Seed the database with all sample data."""
    print("Creating tables...")
    await create_tables()

    print("Seeding customers...")
    await seed_customers()

    print("Seeding products...")
    await seed_products()

    print("Seeding orders...")
    await seed_orders()

    print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())