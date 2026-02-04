from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv
import math

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def calculate_market_stats(cars):
    """
    Calculates the Line of Best Fit (Linear Regression) for Price vs. Mileage.
    Returns slope (m) and y-intercept (b).
    """
    # Filter valid data points
    points = []
    for car in cars:
        try:
            p = int(car['price'].replace('$', '').replace(',', ''))
            m = int(car['mileage'].replace('km', '').replace(',', ''))
            if p > 0 and m > 0:
                points.append((m, p))
        except:
            continue

    n = len(points)
    if n < 2: return 0, 0

    # Statistical sums
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_xx = sum(p[0] ** 2 for p in points)

    # Calculate slope (m) and intercept (b)
    # Formula: m = (N*Σxy - Σx*Σy) / (N*Σx^2 - (Σx)^2)
    numerator = (n * sum_xy) - (sum_x * sum_y)
    denominator = (n * sum_xx) - (sum_x ** 2)
    
    if denominator == 0: return 0, 0

    m = numerator / denominator
    b = (sum_y - (m * sum_x)) / n
    
    return m, b

@app.get("/cars")
def get_cars():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, price, mileage, link, created_at FROM cars ORDER BY created_at DESC;")
        rows = cur.fetchall()
        
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
            
        slope, intercept = calculate_market_stats(cars)
        
        for car in cars:
            try:
                real_price = int(car['price'].replace('$', '').replace(',', ''))
                mileage = int(car['mileage'].replace('km', '').replace(',', ''))
                
                # Predict fair price based on mileage
                # y = mx + b
                fair_price = (slope * mileage) + intercept
                
                diff = fair_price - real_price
                
                if diff > 3000:
                    car['deal_rating'] = "GREAT DEAL"
                    car['deal_color'] = "green"
                elif diff > 500:
                    car['deal_rating'] = "GOOD DEAL"
                    car['deal_color'] = "teal"
                elif diff < -3000:
                    car['deal_rating'] = "OVERPRICED"
                    car['deal_color'] = "red"
                else:
                    car['deal_rating'] = "FAIR PRICE"
                    car['deal_color'] = "gray"
                    
            except:
                car['deal_rating'] = "UNKNOWN"
                car['deal_color'] = "gray"

        cur.close()
        conn.close()
        return cars
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)