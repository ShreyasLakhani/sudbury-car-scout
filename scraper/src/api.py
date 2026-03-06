from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
import uvicorn

load_dotenv()
app = FastAPI()

# 1. Models and Middleware
class Alert(BaseModel):
    email: str
    target_price: int
    keyword: str

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 2. Helper Functions
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def analyze_market(cars):
    df = pd.DataFrame(cars)
    if len(df) < 5: return None 

    df['p_val'] = df['price'].astype(str).str.replace(r'[$,]', '', regex=True).astype(float)
    df['m_val'] = df['mileage'].astype(str).str.replace(r'[km,]', '', regex=True).astype(float)
    
    model = RandomForestRegressor(n_estimators=100)
    model.fit(df[['m_val']], df['p_val'])
    return model

# 3. Routes
@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Sudbury Car Scout API"}

@app.get("/cars")
def get_listings():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, price, mileage, link FROM cars ORDER BY created_at DESC;")
            rows = cur.fetchall()
            
    cars = [{"id": r[0], "title": r[1], "price": r[2], "mileage": r[3], "link": r[4]} for r in rows]
    
    # Architecture note: This is still running synchronously on every page load.
    model = analyze_market(cars)
    if model:
        for car in cars:
            try:
                m_val = float(car['mileage'].replace('km', '').replace(',', ''))
                p_val = float(car['price'].replace('$', '').replace(',', ''))
                fair_price = model.predict(pd.DataFrame([[m_val]], columns=['m_val']))[0]
                diff = fair_price - p_val
                
                if diff > 3000: 
                    car['deal_rating'], car['deal_color'] = "GREAT DEAL", "green"
                elif diff > 500: 
                    car['deal_rating'], car['deal_color'] = "GOOD DEAL", "teal"
                elif diff < -3000: 
                    car['deal_rating'], car['deal_color'] = "OVERPRICED", "red"
                else: 
                    car['deal_rating'], car['deal_color'] = "FAIR PRICE", "gray"
            except (ValueError, KeyError, TypeError) as e:
                print(f"Error processing car {car.get('id')}: {e}")
                car['deal_rating'], car['deal_color'] = "UNKNOWN", "gray"
                
    return cars

@app.post("/alert")
def create_alert(alert: Alert):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO price_alerts (email, target_price, keyword) VALUES (%s, %s, %s)",
                (alert.email, alert.target_price, alert.keyword)
            )
        conn.commit()
    return {"status": "success"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)