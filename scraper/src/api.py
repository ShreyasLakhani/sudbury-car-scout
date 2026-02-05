from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PriceAlert(BaseModel):
    email: str
    target_price: int
    keyword: str

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def train_model(cars):
    df = pd.DataFrame(cars)
    if df.empty: return None

    df['price'] = df['price'].astype(str).str.replace(r'[$,]', '', regex=True)
    df['mileage'] = df['mileage'].astype(str).str.replace(r'[km,]', '', regex=True)
    
    df = df[pd.to_numeric(df['price'], errors='coerce').notnull()]
    df = df[pd.to_numeric(df['mileage'], errors='coerce').notnull()]
    
    if len(df) < 5: return None 
    
    df['price'] = df['price'].astype(float)
    df['mileage'] = df['mileage'].astype(float)
    
    X = df[['mileage']]
    y = df['price']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

@app.get("/cars")
def get_cars():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, price, mileage, link FROM cars ORDER BY created_at DESC;")
    rows = cur.fetchall()
    
    cars = []
    for row in rows:
        cars.append({
            "id": row[0],
            "title": row[1],
            "price": row[2],
            "mileage": row[3],
            "link": row[4]
        })
    
    model = train_model(cars)
    
    for car in cars:
        try:
            if model:
                m_val = float(car['mileage'].replace('km', '').replace(',', ''))
                real_price = float(car['price'].replace('$', '').replace(',', ''))
                predicted = model.predict([[m_val]])[0]
                diff = predicted - real_price
                
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
            pass

    cur.close()
    conn.close()
    return cars

@app.post("/alert")
def set_alert(alert: PriceAlert):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO price_alerts (email, target_price, car_title_keyword) VALUES (%s, %s, %s)",
        (alert.email, alert.target_price, alert.keyword)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)