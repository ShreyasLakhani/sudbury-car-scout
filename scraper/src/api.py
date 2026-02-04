from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS (Allows your React app on port 5173 to talk to this Python app on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@app.get("/cars")
def get_cars():
    """
    Fetches all cars from the Neon Postgres database.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, price, mileage, link, created_at FROM cars ORDER BY created_at DESC;")
        rows = cur.fetchall()
        
        # Convert list of tuples to list of dictionaries (JSON friendly)
        cars = []
        for row in rows:
            cars.append({
                "id": row[0],
                "title": row[1],
                "price": row[2],
                "mileage": row[3],
                "link": row[4],
                "date": str(row[5])
            })
            
        cur.close()
        conn.close()
        return cars
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)