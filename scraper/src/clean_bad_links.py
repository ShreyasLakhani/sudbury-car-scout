import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def clean_database():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    print("Checking for broken links...")

    # 1. Count how many bad cars exist
    cur.execute("SELECT COUNT(*) FROM cars WHERE link = '#' OR link NOT LIKE 'http%';")
    bad_count = cur.fetchone()[0]

    if bad_count > 0:
        print(f"Found {bad_count} cars with broken links. Deleting them...")
        
        # 2. Delete them
        cur.execute("DELETE FROM cars WHERE link = '#' OR link NOT LIKE 'http%';")
        conn.commit()
        print("Success! Broken cars removed.")
    else:
        print("Database is already clean! No broken links found.")

    # 3. Show remaining cars
    cur.execute("SELECT COUNT(*) FROM cars;")
    total = cur.fetchone()[0]
    print(f"Total valid cars remaining: {total}")

    conn.close()

if __name__ == "__main__":
    clean_database()