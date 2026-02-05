import os
import psycopg2
from dotenv import load_dotenv
import json

load_dotenv()

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Clean Schema (No Images)
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
            car_title_keyword TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def save_cars_to_db(cars_data):
    conn = get_db_connection()
    cur = conn.cursor()
    
    new_count = 0
    
    for car in cars_data:
        if not car.get('link') or car['link'] == "#":
            continue

        # Check if exists (Deduplication)
        cur.execute("SELECT id FROM cars WHERE link = %s", (car['link'],))
        exists = cur.fetchone()
        
        if not exists:
            try:
                cur.execute("""
                    INSERT INTO cars (title, price, mileage, link)
                    VALUES (%s, %s, %s, %s)
                """, (car['title'], car['price'], car['mileage'], car['link']))
                new_count += 1
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                continue
            
    conn.commit()
    cur.close()
    conn.close()
    print(f"[DB] Inserted {new_count} new cars.")

if __name__ == "__main__":
    init_db()
    try:
        with open("cars.json", "r") as f:
            data = json.load(f)
            save_cars_to_db(data)
    except FileNotFoundError:
        print("[DB] cars.json not found.")