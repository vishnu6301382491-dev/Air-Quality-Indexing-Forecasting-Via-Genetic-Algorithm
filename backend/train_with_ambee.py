"""
Fetch real historical AQI data from Ambee API and train GA-KELM model
"""
import requests
import time
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from model import train_model, get_model_info, get_model
from database import save_data

load_dotenv()
logger = logging.getLogger(__name__)

# Ambee API Configuration
AMBEE_API_KEY = os.getenv("AMBEE_API_KEY")
AMBEE_BASE_URL = "https://api.ambeedata.com"

# Headers for Ambee API
HEADERS = {"x-api-key": AMBEE_API_KEY, "Content-type": "application/json"}

# Indian cities with coordinates for data collection
CITIES = [
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
    {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
    {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
    {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
    {"name": "Ongole", "lat": 15.5057, "lon": 80.0499},
    {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480},
    {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
    {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126},
    {"name": "Patna", "lat": 25.5941, "lon": 85.1376},
    {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
    {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
    {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
]


def get_aqi_category(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    else: return "Hazardous"


def fetch_current_aqi(lat: float, lon: float, city_name: str) -> dict:
    """Fetch current AQI from Ambee for coordinates"""
    if not AMBEE_API_KEY:
        logger.warning("AMBEE_API_KEY not set")
        return None
    try:
        url = f"{AMBEE_BASE_URL}/latest/by-lat-lng"
        params = {"lat": lat, "lng": lon}

        response = requests.get(url, headers=HEADERS, params=params, timeout=15)

        if response.status_code != 200:
            logger.info("  [SKIP] %s: HTTP %s", city_name, response.status_code)
            return None

        data = response.json()

        if "stations" not in data or len(data["stations"]) == 0:
            logger.info("  [SKIP] %s: No station data", city_name)
            return None

        station = data["stations"][0]

        result = {
            "aqi": station.get("AQI", 0),
            "pm25": station.get("PM25", 0),
            "pm10": station.get("PM10", 0),
            "no2": station.get("NO2", 0),
            "o3": station.get("OZONE", 0),
            "so2": station.get("SO2", 0),
            "co": station.get("CO", 0),
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "source": "Ambee",
            "timestamp": datetime.now().isoformat()
        }

        aqi = result["aqi"]
        result["category"] = get_aqi_category(aqi)
        return result

    except Exception as e:
        logger.warning("  [ERROR] %s: %s", city_name, e)
        return None


def fetch_historical_aqi(lat: float, lon: float, city_name: str, from_date: str, to_date: str) -> list:
    """Fetch historical AQI from Ambee"""
    if not AMBEE_API_KEY:
        return []
    try:
        url = f"{AMBEE_BASE_URL}/history/by-lat-lng"
        params = {"lat": lat, "lng": lon, "from": from_date, "to": to_date}

        response = requests.get(url, headers=HEADERS, params=params, timeout=30)

        if response.status_code != 200:
            logger.info("  [SKIP] %s history: HTTP %s", city_name, response.status_code)
            return []

        data = response.json()
        if "history" not in data:
            return []

        results = []
        for entry in data["history"]:
            result = {
                "aqi": entry.get("AQI", 0),
                "pm25": entry.get("PM25", 0),
                "pm10": entry.get("PM10", 0),
                "no2": entry.get("NO2", 0),
                "o3": entry.get("OZONE", 0),
                "so2": entry.get("SO2", 0),
                "co": entry.get("CO", 0),
                "city": city_name,
                "latitude": lat,
                "longitude": lon,
                "source": "Ambee Historical",
                "timestamp": entry.get("time", datetime.now().isoformat()),
                "category": get_aqi_category(entry.get("AQI", 0))
            }
            results.append(result)

        return results

    except Exception as e:
        logger.warning("  [ERROR] %s history: %s", city_name, e)
        return []


def fetch_all_cities_current():
    """Fetch current AQI from all cities"""
    all_data = []
    logger.info("[FETCH] Fetching current AQI data from Ambee API...")

    for city in CITIES:
        result = fetch_current_aqi(city["lat"], city["lon"], city["name"])
        if result and result["aqi"] > 0:
            all_data.append(result)
            save_data(result)
            logger.info("  [OK] %s: AQI=%s, PM2.5=%s", city['name'], result['aqi'], result['pm25'])
        time.sleep(0.5)

    logger.info("[DONE] Fetched %s current data points", len(all_data))
    return all_data


def train_with_ambee_data():
    """Fetch all available data and train the model"""
    logger.info("GA-KELM Model Training with Ambee AQI Data")

    all_data = fetch_all_cities_current()

    logger.info("[DATA] Total data points collected: %s", len(all_data))

    if len(all_data) < 20:
        logger.warning("Not enough data. Using existing database records...")

    logger.info("[TRAIN] Training GA-KELM model...")
    result = train_model(all_data)

    logger.info("Training Result")
    for key, value in result.items():
        logger.info("  %s: %s", key, value)

    model = get_model()
    logger.info("Model Status:")
    logger.info("  Trained: %s", model.is_trained)
    if model.is_trained:
        logger.info("  RMSE: %.4f", model.training_rmse)
        logger.info("  R2 Score: %.4f", model.training_r2)
        logger.info("  Data Count: %s", model.data_count)
        logger.info("  Trained At: %s", model.trained_at)

    logger.info("[SUCCESS] Model training complete!")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_with_ambee_data()
