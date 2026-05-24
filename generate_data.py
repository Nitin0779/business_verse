"""
BusinessVerse - Sample Data Generator
Generates realistic business datasets for sales, customers, and products.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# ─── Configuration ────────────────────────────────────────────────────────────
REGIONS = ["North", "South", "East", "West", "Central"]
CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Food & Beverage", "Automotive"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer", "Cash"]
STATUS_OPTIONS = ["Delivered", "Shipped", "Processing", "Cancelled", "Returned"]

PRODUCTS = {
    "Electronics": [
        ("Laptop Pro 15", 1200, 750), ("Wireless Headphones", 199, 80),
        ("Smart Watch Ultra", 349, 140), ("Bluetooth Speaker", 89, 35),
        ("4K Monitor 27\"", 450, 220), ("Gaming Mouse", 79, 28),
        ("Mechanical Keyboard", 129, 52), ("Webcam HD 1080p", 69, 25),
        ("USB-C Hub 7-in-1", 59, 20), ("External SSD 1TB", 149, 65)
    ],
    "Clothing": [
        ("Classic White Shirt", 49, 15), ("Denim Jeans Slim", 79, 28),
        ("Casual Sneakers", 95, 40), ("Wool Winter Coat", 189, 75),
        ("Sport T-Shirt", 35, 12), ("Leather Belt", 45, 18),
        ("Formal Trousers", 89, 35), ("Polo Shirt Premium", 65, 22),
        ("Running Shorts", 42, 15), ("Knit Sweater", 75, 30)
    ],
    "Home & Garden": [
        ("Robot Vacuum Cleaner", 299, 140), ("Air Purifier Pro", 249, 110),
        ("Coffee Maker Deluxe", 129, 52), ("Electric Kettle 1.7L", 49, 18),
        ("Blender Pro 1000W", 89, 35), ("Plant Pot Set x3", 39, 14),
        ("LED Desk Lamp", 45, 18), ("Storage Ottoman", 75, 32),
        ("Throw Blanket Soft", 55, 20), ("Garden Hose 50ft", 65, 28)
    ],
    "Sports": [
        ("Yoga Mat Premium", 45, 18), ("Resistance Bands Set", 29, 10),
        ("Dumbbell Set 20kg", 89, 42), ("Cycling Helmet", 79, 32),
        ("Running Shoes Pro", 129, 55), ("Gym Gloves", 25, 9),
        ("Jump Rope Speed", 19, 7), ("Foam Roller", 35, 12),
        ("Pull-Up Bar", 55, 22), ("Water Bottle 1L", 22, 8)
    ],
    "Books": [
        ("Business Analytics Guide", 45, 12), ("Python Programming", 55, 15),
        ("Data Science Handbook", 65, 18), ("Marketing Strategy", 38, 10),
        ("Leadership Principles", 32, 8), ("Finance for Managers", 48, 13),
        ("Machine Learning A-Z", 72, 20), ("SQL Mastery", 42, 11),
        ("Entrepreneurship Now", 36, 9), ("Digital Marketing", 40, 11)
    ],
    "Food & Beverage": [
        ("Premium Coffee Beans 1kg", 32, 10), ("Organic Green Tea 100g", 18, 5),
        ("Protein Powder Vanilla", 55, 20), ("Mixed Nuts 500g", 24, 8),
        ("Olive Oil Extra Virgin", 28, 9), ("Dark Chocolate Bar 72%", 12, 4),
        ("Granola Bars x12", 22, 7), ("Almond Milk 1L", 8, 2),
        ("Energy Drink Pack x24", 35, 12), ("Collagen Powder 300g", 45, 16)
    ],
    "Automotive": [
        ("Car Dash Cam 4K", 99, 42), ("Tire Inflator Auto", 45, 18),
        ("Car Phone Mount", 25, 9), ("Seat Covers Set", 79, 32),
        ("Jump Starter Pack", 89, 38), ("Car Vacuum Cleaner", 55, 22),
        ("Steering Wheel Cover", 29, 11), ("Car Air Freshener x5", 15, 5),
        ("LED Car Lights Kit", 35, 14), ("Car Wax Premium", 28, 10)
    ]
}

CUSTOMER_NAMES = [
    "James Wilson", "Emily Chen", "Michael Brown", "Sarah Johnson", "David Lee",
    "Jessica Martinez", "Robert Taylor", "Amanda Davis", "Christopher Anderson", "Lauren Thomas",
    "Daniel Jackson", "Nicole White", "Matthew Harris", "Rachel Clark", "Andrew Lewis",
    "Stephanie Robinson", "Joshua Walker", "Megan Hall", "Ryan Allen", "Ashley Young",
    "Kevin King", "Brittany Wright", "Brandon Scott", "Amber Green", "Tyler Adams",
    "Melissa Baker", "Aaron Nelson", "Heather Carter", "Adam Mitchell", "Danielle Perez",
    "Jonathan Roberts", "Crystal Turner", "Nathan Phillips", "Monica Campbell", "Samuel Parker",
    "Vanessa Evans", "Benjamin Edwards", "Alicia Collins", "Gregory Stewart", "Tiffany Sanchez",
    "Patrick Morris", "Kayla Rogers", "Eric Reed", "Andrea Cook", "Steven Morgan",
    "Jennifer Bell", "Timothy Murphy", "Laura Bailey", "Kenneth Rivera", "Sharon Cooper"
]


def generate_customers(n=500):
    """Generate realistic customer dataset."""
    customers = []
    start_date = datetime(2022, 1, 1)
    
    for i in range(1, n + 1):
        name = CUSTOMER_NAMES[i % len(CUSTOMER_NAMES)] + (f" {i // len(CUSTOMER_NAMES) + 1}" if i >= len(CUSTOMER_NAMES) else "")
        first, last = name.split(" ", 1)
        email = f"{first.lower()}.{last.lower().replace(' ', '')}{i}@email.com"
        
        registration_date = start_date + timedelta(days=random.randint(0, 900))
        age = random.randint(22, 68)
        region = random.choice(REGIONS)
        
        # Churn label: older customers with fewer orders more likely to churn
        purchase_freq = random.randint(1, 30)
        avg_spend = round(random.uniform(50, 2000), 2)
        last_purchase_days = random.randint(1, 400)
        support_tickets = random.randint(0, 8)
        satisfaction = random.randint(1, 10)
        
        # Churn probability calculation
        churn_score = (last_purchase_days / 400) * 0.4 + (support_tickets / 8) * 0.3 + ((10 - satisfaction) / 10) * 0.3
        churn = 1 if churn_score > 0.5 else 0
        
        customers.append({
            "customer_id": f"CUST{i:04d}",
            "name": name,
            "email": email,
            "age": age,
            "region": region,
            "registration_date": registration_date.strftime("%Y-%m-%d"),
            "purchase_frequency": purchase_freq,
            "avg_order_value": avg_spend,
            "last_purchase_days_ago": last_purchase_days,
            "support_tickets": support_tickets,
            "satisfaction_score": satisfaction,
            "total_spent": round(avg_spend * purchase_freq * random.uniform(0.8, 1.2), 2),
            "churn": churn
        })
    
    return pd.DataFrame(customers)


def generate_products():
    """Generate product dataset."""
    products = []
    product_id = 1
    
    for category, items in PRODUCTS.items():
        for name, price, cost in items:
            products.append({
                "product_id": f"PROD{product_id:03d}",
                "product_name": name,
                "category": category,
                "price": price,
                "cost": cost,
                "profit_margin": round((price - cost) / price * 100, 2),
                "stock_quantity": random.randint(20, 500),
                "supplier": f"Supplier {random.randint(1, 20):02d}",
                "rating": round(random.uniform(3.5, 5.0), 1)
            })
            product_id += 1
    
    return pd.DataFrame(products)


def generate_orders(customers_df, products_df, n=5000):
    """Generate orders dataset linking customers and products."""
    orders = []
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days
    
    for i in range(1, n + 1):
        customer = customers_df.sample(1).iloc[0]
        product = products_df.sample(1).iloc[0]
        
        order_date = start_date + timedelta(days=random.randint(0, date_range))
        quantity = random.randint(1, 5)
        unit_price = product["price"] * random.uniform(0.9, 1.1)  # slight price variation
        discount = random.choice([0, 0, 0, 5, 10, 15, 20]) / 100
        total = round(unit_price * quantity * (1 - discount), 2)
        cost_total = round(product["cost"] * quantity, 2)
        profit = round(total - cost_total, 2)
        
        orders.append({
            "order_id": f"ORD{i:05d}",
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "category": product["category"],
            "region": customer["region"],
            "order_date": order_date.strftime("%Y-%m-%d"),
            "quantity": quantity,
            "unit_price": round(unit_price, 2),
            "discount_pct": discount * 100,
            "total_amount": total,
            "cost": cost_total,
            "profit": profit,
            "payment_method": random.choice(PAYMENT_METHODS),
            "status": random.choices(
                STATUS_OPTIONS,
                weights=[60, 15, 10, 10, 5]
            )[0]
        })
    
    return pd.DataFrame(orders)


def main():
    """Generate all datasets and save to CSV."""
    os.makedirs("data", exist_ok=True)
    
    print("Generating customers dataset...")
    customers_df = generate_customers(500)
    customers_df.to_csv("data/customers.csv", index=False)
    print(f"  [OK] customers.csv - {len(customers_df)} rows")
    
    print("Generating products dataset...")
    products_df = generate_products()
    products_df.to_csv("data/products.csv", index=False)
    print(f"  [OK] products.csv - {len(products_df)} rows")
    
    print("Generating orders dataset...")
    orders_df = generate_orders(customers_df, products_df, 5000)
    orders_df.to_csv("data/orders.csv", index=False)
    print(f"  [OK] orders.csv - {len(orders_df)} rows")
    
    print("\nAll datasets generated successfully!")
    print(f"Data saved to: {os.path.abspath('data')}")
    
    print("\n--- Summary ---")
    print(f"Total Revenue:   ${orders_df['total_amount'].sum():,.2f}")
    print(f"Total Orders:    {len(orders_df):,}")
    print(f"Total Customers: {len(customers_df):,}")
    print(f"Total Products:  {len(products_df):,}")
    print(f"Total Profit:    ${orders_df['profit'].sum():,.2f}")


if __name__ == "__main__":
    main()
