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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Alert(BaseModel):
    email: str
    target_price: int
    keyword: str

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

@app.get("/cars")
def get_listings():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, price, mileage, link FROM cars ORDER BY created_at DESC;")
    rows = cur.fetchall()
    conn.close()
    
    cars = [{"id": r[0], "title": r[1], "price": r[2], "mileage": r[3], "link": r[4]} for r in rows]
    
    model = analyze_market(cars)
    if model:
        for car in cars:
            try:
                m_val = float(car['mileage'].replace('km', '').replace(',', ''))
                p_val = float(car['price'].replace('$', '').replace(',', ''))
                fair_price = model.predict([[m_val]])[0]
                diff = fair_price - p_val
                
                if diff > 3000: car['deal_rating'] = "GREAT DEAL"; car['deal_color'] = "green"
                elif diff > 500: car['deal_rating'] = "GOOD DEAL"; car['deal_color'] = "teal"
                elif diff < -3000: car['deal_rating'] = "OVERPRICED"; car['deal_color'] = "red"
                else: car['deal_rating'] = "FAIR PRICE"; car['deal_color'] = "gray"
            except: pass
            
    return cars

@app.post("/alert")
def create_alert(alert: Alert):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO price_alerts (email, target_price, keyword) VALUES (%s, %s, %s)",
        (alert.email, alert.target_price, alert.keyword)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)