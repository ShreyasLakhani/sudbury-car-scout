import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv()

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            price TEXT NOT NULL,
            mileage TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            target_price INTEGER NOT NULL,
            keyword TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    conn.close()

def load_data():
    conn = get_db()
    cur = conn.cursor()
    
    try:
        with open("cars.json", "r") as f:
            cars = json.load(f)
            
        new_count = 0
        for car in cars:
            cur.execute("SELECT id FROM cars WHERE link = %s", (car['link'],))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO cars (title, price, mileage, link)
                    VALUES (%s, %s, %s, %s)
                """, (car['title'], car['price'], car['mileage'], car['link']))
                new_count += 1
        
        conn.commit()
        print(f"✅ Database Sync: Added {new_count} new listings.")
        
    except FileNotFoundError:
        print("⚠️ No cars.json found. Run the scraper first.")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    load_data()