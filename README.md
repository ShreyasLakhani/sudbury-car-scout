# Sudbury Car Scout AI 🚗

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-green.svg)
![React](https://img.shields.io/badge/React-18+-61dafb.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

AI-powered car listing aggregator and market analysis tool for Sudbury, Ontario. Scrapes AutoTrader listings, performs machine learning-based price analysis, and provides real-time market insights.

## 🌐 Live Demo

- **Frontend**: https://sudbury-car-scout-nnmp.vercel.app
- **API Endpoint**: https://sudbury-car-scout-production.up.railway.app/cars
- **Status**: ✅ Production Ready

## Features

- **Web Scraping**: Automated scraping from AutoTrader for Sudbury area
- **AI Price Analysis**: Random Forest ML model for fair price prediction
- **Market Visualization**: Interactive scatter plots showing price vs mileage correlation
- **Price Alerts**: Set notifications for specific cars below target prices
- **Deal Detection**: Automatic classification of listings (Great Deal, Fair Price, Overpriced)

## ⚡ Quick Start

**Just want to see it?** Visit the [live demo](https://sudbury-car-scout-nnmp.vercel.app)

**Want to run locally?**

```bash
# 1. Backend
cd scraper
pip install -r requirements.txt
# Create .env file with your DATABASE_URL
python src/api.py

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev

# 3. Visit http://localhost:5173
```

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Database (via Neon.tech)
- **Selenium**: Browser automation for scraping
- **scikit-learn**: Machine learning for price prediction
- **Pandas**: Data processing and analysis

### Frontend
- **React + Vite**: Modern frontend framework
- **Mantine UI**: Component library
- **Recharts**: Data visualization

### DevOps
- **Docker**: Containerization ready
- **pytest**: Automated testing

## Project Structure

```
sudbury-car-scout/
├── scraper/                # Backend & scraping logic
│   ├── src/
│   │   ├── main.py        # Web scraper
│   │   ├── api.py         # FastAPI endpoints
│   │   ├── db.py          # Database operations
│   │   └── ml.py          # ML price prediction
│   ├── requirements.txt   # Python dependencies
│   ├── .env.example       # Environment template
│   └── Dockerfile         # Backend container
├── frontend/              # React application
│   ├── src/
│   │   ├── App.jsx        # Main component
│   │   └── main.jsx       # Entry point
│   ├── package.json       # Node dependencies
│   └── .env.example       # Frontend environment template
├── tests/                 # Test suite
│   └── test_api.py        # API tests
└── docker-compose.yml     # Multi-container setup
```

## Installation & Setup

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL database** (or use Neon.tech free tier)
- **Chrome browser** (for web scraping)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/sudbury-car-scout.git
cd sudbury-car-scout
```

### 2. Backend Setup

```bash
cd scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your DATABASE_URL
```

**Configure `.env` file:**
```env
DATABASE_URL=postgresql://username:password@host:5432/database?sslmode=require
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
```

**Initialize database:**
```bash
python src/db.py
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional)
cp .env.example .env
# Edit .env if your backend runs on different port
```

### 4. Run the Application

**Terminal 1 - Start Backend:**
```bash
cd scraper/src
python api.py
# API will run on http://localhost:8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
# Frontend will run on http://localhost:5173
```

**Terminal 3 - Run Scraper (optional):**
```bash
cd scraper
python src/main.py
# Scrapes fresh data from AutoTrader
# You'll need to manually solve the captcha when prompted
```

## Usage

1. **View Listings**: Open http://localhost:5173 to see all scraped car listings
2. **Market Analysis**: View the interactive scatter chart showing price vs mileage trends
3. **Set Alerts**: Click "Set Price Alert" to get notified when cars matching your criteria appear
4. **Deal Detection**: Each listing shows an AI-powered badge (Great Deal, Fair Price, Overpriced)

## API Endpoints

### `GET /cars`
Returns all car listings with AI analysis

**Response:**
```json
[
  {
    "id": 1,
    "title": "2018 Honda Civic LX",
    "price": "$15,900",
    "mileage": "85,000 km",
    "link": "https://...",
    "deal_rating": "GREAT DEAL",
    "deal_color": "green"
  }
]
```

### `POST /alert`
Create a price alert

**Request:**
```json
{
  "email": "user@example.com",
  "target_price": 20000,
  "keyword": "Civic"
}
```

**Response:**
```json
{
  "status": "success"
}
```

## Testing

```bash
# Run backend tests (from project root)
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=scraper.src tests/
```

## Deployment

### Option 1: Local Development
Follow the installation steps above.

### Option 2: Docker (Recommended for Production)

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

### Option 3: Cloud Deployment

**Current Production Stack:**
- **Backend**: Railway (https://sudbury-car-scout-production.up.railway.app)
- **Frontend**: Vercel (https://sudbury-car-scout-nnmp.vercel.app)
- **Database**: Neon.tech PostgreSQL

**To deploy your own instance:**

**Backend (Railway):**
1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Set root directory to `scraper`
4. Add environment variables:
   - `DATABASE_URL`: Your Neon.tech PostgreSQL connection string
   - `ALLOWED_ORIGINS`: Your Vercel frontend URL (e.g., `https://your-app.vercel.app`)
5. Deploy command: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
6. Railway will auto-deploy on every git push

**Frontend (Vercel):**
1. Import your GitHub repo to [Vercel](https://vercel.com)
2. Set root directory to `frontend`
3. Add environment variable:
   - `VITE_API_URL`: Your Railway backend URL
4. Build command: `npm run build`
5. Output directory: `dist`
6. Auto-deploys on git push to main branch

**Database (Neon.tech):**
1. Create free account at [Neon.tech](https://neon.tech)
2. Create a new PostgreSQL database
3. Copy connection string (format: `postgresql://user:pass@host:5432/db?sslmode=require`)
4. Run `python src/db.py` to initialize tables

## Database Schema

### `cars` Table
```sql
CREATE TABLE cars (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    price TEXT NOT NULL,
    mileage TEXT NOT NULL,
    link TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `price_alerts` Table
```sql
CREATE TABLE price_alerts (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    target_price INTEGER NOT NULL,
    keyword TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Machine Learning Model

The application uses a **Random Forest Regressor** to predict fair market prices based on mileage. The model:

1. Trains on all scraped listings
2. Uses mileage as the primary feature
3. Predicts expected price for each vehicle
4. Compares predicted vs actual price to classify deals

**Deal Classification:**
- Great Deal: $3000+ below predicted price
- Good Deal: $500-$3000 below predicted price
- Fair Price: Within $500 of predicted price
- Overpriced: $3000+ above predicted price

## Environment Variables

### Backend (`scraper/.env`)
```env
DATABASE_URL=postgresql://...
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.com
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is correct in `scraper/.env`
- Check if PostgreSQL is running
- For Neon.tech, ensure `?sslmode=require` is in the URL

### CORS Errors
- Add your frontend URL to `ALLOWED_ORIGINS` in backend `.env`
- Restart the backend server after changing `.env`

### Scraper Not Working
- Ensure Chrome browser is installed
- Check if AutoTrader changed their HTML structure
- You may need to manually solve captchas
- Run with `python src/main.py` and monitor console output

### Frontend Can't Connect to API
- Verify backend is running on port 8000
- Check `VITE_API_URL` in frontend `.env`
- Ensure CORS is properly configured

## ⚠️ Known Limitations

- **Manual CAPTCHA**: AutoTrader may occasionally require manual CAPTCHA solving (typically on first run or after extended use)
- **Data Size**: Price predictions work best with 20+ listings in database
- **Geographic Scope**: Currently optimized for Sudbury, Ontario area only
- **Site Changes**: AutoTrader HTML structure changes may require scraper updates
- **Scraping Speed**: Initial data collection takes 2-5 minutes
- **Alert System**: Price alert notifications require manual implementation (email setup needed)

## ⚙️ Performance Notes

- **Scraping**: Initial data collection: ~2-5 minutes depending on listing count
- **API Response**: Typical response time < 100ms for `/cars` endpoint
- **Database**: Queries optimized with indexes on frequently accessed columns
- **Frontend**: Lazy loading and React optimizations for smooth UX
- **ML Model**: Training happens on-the-fly, minimal latency (~50ms)

## 🗺️ Roadmap

- [ ] Email notifications for price alerts
- [ ] Support for additional data sources (Kijiji, Facebook Marketplace)
- [ ] Mobile-responsive design improvements
- [ ] Advanced filtering (year range, make, model, body type)
- [ ] Historical price tracking and trends
- [ ] Automated CAPTCHA solving
- [ ] Multi-city support across Canada
- [ ] User authentication and saved searches
- [ ] API rate limiting and caching

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Open a Pull Request

## License

MIT License - feel free to use this project for your own purposes.

## Acknowledgments

- AutoTrader for listing data
- Neon.tech for free PostgreSQL hosting
- Built with FastAPI, React, and scikit-learn

## Contact

For issues or questions, please open a GitHub issue.

---

**Made with ❤️ for the Sudbury community**
