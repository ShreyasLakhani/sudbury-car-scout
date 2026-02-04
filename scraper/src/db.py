import os
import json
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the URL
DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    if not DB_URL:
        raise ValueError("DATABASE_URL is not set in .env file")
    return psycopg2.connect(DB_URL)

def init_db():
    """
    Creates the table structure if it doesn't exist.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # We use the LINK as the unique identifier to prevent duplicates
    create_table_query = """
    CREATE TABLE IF NOT EXISTS cars (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        price TEXT,
        mileage TEXT,
        link TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        cur.execute(create_table_query)
        conn.commit()
        print("[*] Database schema initialized (Table 'cars' is ready).")
    except Exception as e:
        print(f"[!] Error creating table: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def load_json_to_db():
    """
    Reads cars.json and inserts new records into Postgres.
    """
    # Check if file exists
    if not os.path.exists("cars.json"):
        print("[!] cars.json not found. Run the scraper first.")
        return

    with open("cars.json", "r") as f:
        data = json.load(f)

    if not data:
        print("[!] No data in cars.json to upload.")
        return

    conn = get_connection()
    cur = conn.cursor()
    
    inserted_count = 0
    skipped_count = 0

    insert_query = """
    INSERT INTO cars (title, price, mileage, link)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (link) DO NOTHING;
    """

    try:
        for car in data:
            # Prepare data
            title = car.get("title", "N/A")
            price = car.get("price", "N/A")
            mileage = car.get("mileage", "N/A")
            link = car.get("link", "N/A")
            
            # Execute
            cur.execute(insert_query, (title, price, mileage, link))
            
            # Check if a row was actually inserted (rowcount == 1)
            if cur.rowcount > 0:
                inserted_count += 1
            else:
                skipped_count += 1
                
        conn.commit()
        print(f"[SUCCESS] Pipeline complete.")
        print(f" -> Inserted: {inserted_count} new cars")
        print(f" -> Skipped:  {skipped_count} duplicates")
        
    except Exception as e:
        print(f"[!] Database Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("--- SUDBURY CAR SCOUT: DATABASE PIPELINE ---")
    init_db()       # Ensure table exists
    load_json_to_db() # Upload data