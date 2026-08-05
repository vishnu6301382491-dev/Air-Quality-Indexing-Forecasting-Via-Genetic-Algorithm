# Real-Time AQI Prediction System

<div align="center">

![AQI](https://img.shields.io/badge/AQI-Prediction-blue?style=for-the-badge)
![GA-KELM](https://img.shields.io/badge/ML-GA--KELM-purple?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge)
![Firebase](https://img.shields.io/badge/Database-Firebase-FFCA28?style=for-the-badge)

**Real-time air quality prediction using Genetic Algorithm optimized Kernel Extreme Learning Machine**

</div>

---

## Features

- **Real-Time AQI Monitoring** - Live updates from WAQI, Ambee, and OpenWeatherMap APIs
- **GA-KELM Predictions** - Advanced ML predictions with 94%+ accuracy
- **Multi-City Support** - Add and compare AQI across multiple cities
- **Location Detection** - Auto-detect user's location
- **24h Trend Charts** - Visual AQI trends with threshold lines
- **Weather Integration** - The Weather Company API for accurate weather data
- **Firebase Database** - Free real-time cloud database
- **Modern Dashboard** - Clean, professional React UI
- **Auto Scheduler** - Automatic data collection every 15 minutes

---

## Screenshots

| Dashboard | Trend Chart |
|-----------|-------------|
| Clean AQI display with city sidebar | 24h trend with threshold lines |

---

## Project Structure

```
AQI-RealTime-System/
├── backend/
│   ├── main.py               # FastAPI server
│   ├── model.py              # GA-KELM ML model
│   ├── data_fetch.py         # Multi-API data fetcher (WAQI, Ambee, OWM)
│   ├── database.py           # Firebase connection
│   ├── scheduler.py          # Auto data update
│   ├── train_model.py        # Model training script
│   ├── train_multi_api.py    # Multi-API training data fetcher
│   ├── requirements.txt
│   ├── .env.example
│   └── firebase-credentials.json  (you create this)
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.js   # Main dashboard
│   │   │   └── HomePage.css
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
│
└── README.md
```

---

## Data Sources

| API | Purpose | Priority |
|-----|---------|----------|
| **WAQI** | Primary AQI data (most accurate) | 1st |
| **Ambee** | Fallback AQI + Historical data | 2nd |
| **OpenWeatherMap** | Weather + AQI fallback | 3rd |
| **The Weather Company** | Enhanced weather data (UV index) | Primary for weather |

---

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Firebase project (free)
- API Keys: WAQI, Ambee, OpenWeatherMap (all free tiers available)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your API keys

# Make sure firebase-credentials.json is in backend folder

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

Frontend runs at: http://localhost:3000

---

## Environment Variables

### Backend (.env)

```env
# Firebase
FIREBASE_URL=https://your-project-id.firebaseio.com
FIREBASE_CRED_PATH=firebase-credentials.json

# API Keys
API_KEY=your_openweathermap_api_key
WAQI_API_KEY=your_waqi_token
AMBEE_API_KEY=your_ambee_api_key
TWC_API_KEY=your_weather_company_key

# Default Location (Ongole, India)
LATITUDE=15.5057
LONGITUDE=80.0499

# CORS
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/current` | Current AQI data (with lat/lon params) |
| GET | `/predict` | GA-KELM prediction |
| GET | `/trend` | 24h AQI trend data for charts |
| GET | `/update` | Fetch fresh data |
| GET | `/history` | Historical readings |
| POST | `/train` | Train the model |
| GET | `/model/info` | Model information |
| GET | `/health` | Detailed health check |

---

## GA-KELM Model

**Genetic Algorithm + Kernel Extreme Learning Machine**

| Metric | Value |
|--------|-------|
| Data Points | 375+ |
| R² Score | 0.946 (94.6%) |
| RMSE | 0.041 |
| Training Time | ~2 minutes |

### How It Works

1. **Data Collection** - Fetches from multiple APIs across Indian cities
2. **Feature Engineering** - Uses PM2.5, PM10, NO2, O3, SO2, CO, weather data
3. **Genetic Algorithm** - Optimizes C (regularization) and gamma (kernel width)
4. **KELM Training** - Fast closed-form solution with RBF kernel
5. **Prediction** - Real-time AQI prediction for next hour

---

## Firebase Setup

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click **"Add Project"** → Enter name → Continue
3. Disable Google Analytics (optional) → Create Project

### Step 2: Create Realtime Database

1. Go to **Build → Realtime Database**
2. Click **"Create Database"**
3. Choose location (us-central1) → Next
4. Select **"Start in test mode"** → Enable

### Step 3: Get Service Account Credentials

1. Go to **Project Settings** → **Service Accounts**
2. Click **"Generate new private key"**
3. Rename to `firebase-credentials.json`
4. Move to `backend/` folder

---

## AQI Categories

| AQI | Category | Color |
|-----|----------|-------|
| 0-50 | Good | Green |
| 51-100 | Moderate | Yellow |
| 101-150 | Unhealthy for Sensitive | Orange |
| 151-200 | Unhealthy | Red |
| 201-300 | Very Unhealthy | Purple |
| 301+ | Hazardous | Maroon |

---

## UI Features

- **City Sidebar** - Add/remove cities, quick switch
- **Auto Location** - Detect user's current location
- **Live Badge** - Real-time data indicator
- **AQI Card** - Large display with category badge
- **Weather Card** - Temperature, humidity, wind, UV
- **Prediction Card** - Next hour prediction with model info
- **Trend Chart** - 24h trend with threshold lines
- **Pollutant Grid** - All 6 pollutants with color indicators
- **City Comparison** - Compare AQI across saved cities

---

## Deployment

### Backend (Railway/Render)

```bash
cd backend
# Deploy to Railway or Render
# Set environment variables in dashboard
```

### Frontend (Vercel)

```bash
cd frontend
npm run build
vercel --prod
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, CSS3 |
| Backend | FastAPI, Python 3.9+ |
| Database | Firebase Realtime DB |
| ML Model | GA-KELM (Scikit-learn) |
| APIs | WAQI, Ambee, OWM, TWC |

---

## License

MIT License

<div align="center">
<strong>Built for cleaner air monitoring</strong>
</div>
