"""
Database initialization and data loading for Car Scout.

Creates tables (cars, price_alerts), performance indexes,
and syncs scraped data from cars.json into PostgreSQL.
"""

import json
import os

import psycopg2
from dotenv import load_dotenv

from logger import get_logger

load_dotenv()
log = get_logger("db")


def get_db():
    """Open a PostgreSQL connection using DATABASE_URL."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        log.error("DATABASE_URL environment variable is not set")
        raise RuntimeError("DATABASE_URL not configured")
    return psycopg2.connect(db_url)


def init_db():
    """Create tables and performance indexes if they don't exist."""
    conn = get_db()
    cur = conn.cursor()

    # --- Tables ---
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

    # --- Performance indexes ---
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_cars_created_at "
        "ON cars (created_at DESC);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_cars_title "
        "ON cars USING gin(to_tsvector('english', title));"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_alerts_email "
        "ON price_alerts (email);"
    )

    conn.commit()
    conn.close()
    log.info("Database tables and indexes initialized successfully")


def load_data():
    """Load scraped cars from cars.json into the database."""
    conn = get_db()
    cur = conn.cursor()

    # Try multiple possible paths for cars.json
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "cars.json"),  # scraper/cars.json
        os.path.join(os.path.dirname(__file__), "..", "..", "cars.json"),  # root/cars.json
        "cars.json",  # current directory
    ]

    cars_file = None
    for path in possible_paths:
        if os.path.exists(path):
            cars_file = path
            break

    try:
        if not cars_file:
            raise FileNotFoundError("cars.json not found in any expected location")

        with open(cars_file, "r", encoding="utf-8") as f:
            cars = json.load(f)

        if not isinstance(cars, list):
            log.error("cars.json does not contain a list")
            return

        new_count = 0
        skipped = 0
        for car in cars:
            # Validate required fields
            if not all(k in car for k in ("title", "price", "mileage", "link")):
                skipped += 1
                continue

            cur.execute("SELECT id FROM cars WHERE link = %s", (car["link"],))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO cars (title, price, mileage, link) "
                    "VALUES (%s, %s, %s, %s)",
                    (car["title"], car["price"], car["mileage"], car["link"]),
                )
                new_count += 1

        conn.commit()
        log.info(
            "Database sync complete — added %d new listings, skipped %d invalid",
            new_count,
            skipped,
        )

    except FileNotFoundError as e:
        log.warning("%s — run the scraper first to generate cars.json", e)
    except json.JSONDecodeError as e:
        log.error("Failed to parse cars.json: %s", e)
    except psycopg2.Error as e:
        conn.rollback()
        log.error("Database error during load: %s", e)
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    load_data()