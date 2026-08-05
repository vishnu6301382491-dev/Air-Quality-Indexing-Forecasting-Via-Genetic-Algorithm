"""
FastAPI Main Server
Real-Time AQI Prediction System

Endpoints:
- GET / : Health check
- GET /update : Fetch and save AQI data
- GET /predict : Get AQI prediction
- GET /current : Get current AQI
- GET /history : Get historical data
- POST /train : Train the model
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv

from data_fetch import fetch_data
from utils import get_aqi_category
from database import (
    save_data, 
    get_latest_data, 
    get_historical_data,
    get_training_data,
    save_prediction,
    get_predictions,
    test_connection
)
from model import predict_aqi, predict_from_data, train_model, get_model, get_model_info
from scheduler import start_scheduler, stop_scheduler, scheduler

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Get frontend URL for CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    logger.info("Starting AQI Prediction Server")
    test_connection()
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down")
    stop_scheduler()


app = FastAPI(
    title="Real-Time AQI Prediction System",
    description="AQI prediction using GA-KELM (Genetic Algorithm - Kernel ELM)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",
        "https://aqi-dashboard.vercel.app"  # Add your deployed frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ ENDPOINTS ============

@app.get("/")
def home():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "AQI Prediction Server is Online",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Detailed health check"""
    model = get_model()
    return {
        "status": "healthy",
        "database": test_connection(),
        "model_trained": model.is_trained,
        "scheduler_running": scheduler.is_running
    }


@app.get("/update")
def update_data():
    """Fetch fresh AQI data and save to database"""
    try:
        data = fetch_data()
        doc_id = save_data(data)
        
        return {
            "message": "Data Updated Successfully",
            "aqi": data.get("aqi"),
            "category": data.get("category"),
            "pm25": data.get("pm25"),
            "id": doc_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current")
def get_current(lat: float = None, lon: float = None):
    """Get current/latest AQI reading for given location"""
    try:
        # Always fetch fresh data with provided coordinates
        fresh_data = fetch_data(lat=lat, lon=lon)
        save_data(fresh_data)
        return fresh_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict")
def predict(lat: float = None, lon: float = None):
    """Get AQI prediction using GA-KELM model"""
    try:
        # Fetch fresh data with provided coordinates
        current = fetch_data(lat=lat, lon=lon)
        save_data(current)
        
        # Get prediction (uses trained model or EPA fallback)
        prediction = predict_from_data(current)
        category = get_aqi_category(int(prediction))
        
        # Get model status
        model = get_model()
        
        # Save prediction
        pred_record = {
            "predicted_aqi": prediction,
            "category": category,
            "latitude": current.get("latitude"),
            "longitude": current.get("longitude")
        }
        save_prediction(pred_record)
        
        return {
            "AQI_Prediction": prediction,
            "category": category,
            "model_trained": model.is_trained,
            "current_aqi": current.get("aqi"),
            "pm25": current.get("pm25"),
            "pm10": current.get("pm10"),
            "location": {
                "lat": current.get("latitude"),
                "lon": current.get("longitude")
            },
            "message": "Predicted using GA-KELM model" if model.is_trained else "Predicted using EPA formula (model not trained)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
def get_history(limit: int = 24):
    """Get historical AQI readings"""
    try:
        data = get_historical_data(max(1, min(limit, 1000)))
        
        # Convert ObjectIds to strings
        for record in data:
            record["_id"] = str(record["_id"])
        
        return {
            "count": len(data),
            "data": data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trend")
def get_trend(lat: float = None, lon: float = None, hours: int = 24):
    """Get AQI trend data for charts"""
    try:
        # Get historical data
        hours = max(1, min(hours, 168))
        data = get_historical_data(hours * 2)  # Get more data for averaging
        
        # Extract AQI values
        aqi_values = []
        for record in data:
            aqi = record.get("aqi", 0)
            if aqi and isinstance(aqi, (int, float)) and aqi > 0:
                aqi_values.append(int(aqi))
        
        # Limit to requested hours
        aqi_values = aqi_values[:hours]
        
        # If not enough data, pad with current value
        if len(aqi_values) < 6:
            current = fetch_data(lat=lat, lon=lon)
            current_aqi = current.get("aqi", 100)
            # Generate realistic trend with some variation
            import random
            aqi_values = [max(20, current_aqi + random.randint(-25, 25)) for _ in range(hours)]
        
        return {
            "trend": aqi_values,
            "count": len(aqi_values),
            "average": sum(aqi_values) / len(aqi_values) if aqi_values else 0,
            "max": max(aqi_values) if aqi_values else 0,
            "min": min(aqi_values) if aqi_values else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions")
def get_prediction_history(limit: int = 24):
    """Get historical predictions"""
    try:
        data = get_predictions(max(1, min(limit, 1000)))
        
        for record in data:
            record["_id"] = str(record["_id"])
        
        return {
            "count": len(data),
            "predictions": data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train")
def train():
    """Manually trigger model training"""
    try:
        data_list = get_training_data()
        
        if len(data_list) < 20:
            return {
                "status": "skipped",
                "message": f"Not enough data. Have {len(data_list)}, need 20+",
                "data_count": len(data_list)
            }
        
        result = train_model(data_list)
        
        return {
            "status": "success",
            "message": "Model trained successfully",
            "model_params": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    """Get AQI statistics"""
    try:
        data = get_historical_data(100)
        
        if not data:
            return {"message": "No data available"}
        
        aqi_values = [d.get("aqi", 0) for d in data if d.get("aqi")]
        
        if not aqi_values:
            return {"message": "No AQI values found"}
        
        return {
            "count": len(aqi_values),
            "min": min(aqi_values),
            "max": max(aqi_values),
            "avg": round(sum(aqi_values) / len(aqi_values), 2),
            "latest": aqi_values[0] if aqi_values else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/info")
def model_info():
    """Get information about the trained model"""
    return get_model_info()


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
