"""
Multi-API AQI Data Fetcher and GA-KELM Model Trainer
Sources: Ambee, WAQI APIs
"""
import requests
import time
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from model import train_model, get_model_info, get_model
from database import save_data

load_dotenv()
logger = logging.getLogger(__name__)

# ============ API KEYS (from environment) ============
AMBEE_API_KEY = os.getenv("AMBEE_API_KEY")
WAQI_API_KEY = os.getenv("WAQI_API_KEY")
AZURE_MAPS_KEY = os.getenv("AZURE_MAPS_KEY")

# ============ CITIES ============
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
    {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
    {"name": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366},
    {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
    {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245},
    {"name": "Raipur", "lat": 21.2514, "lon": 81.6296},
]


def get_aqi_category(aqi):
    """Get AQI category based on value"""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


# ============ AMBEE API ============
def fetch_from_ambee(lat, lon, city_name):
    """Fetch current AQI from Ambee API"""
    if not AMBEE_API_KEY:
        return None
    try:
        url = "https://api.ambeedata.com/latest/by-lat-lng"
        headers = {"x-api-key": AMBEE_API_KEY, "Content-type": "application/json"}
        params = {"lat": lat, "lng": lon}

        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code != 200:
            return None

        data = response.json()

        if "stations" not in data or len(data["stations"]) == 0:
            return None

        station = data["stations"][0]

        return {
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
            "category": get_aqi_category(station.get("AQI", 0)),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.warning("Ambee error for %s: %s", city_name, e)
        return None


# ============ WAQI API ============
def fetch_from_waqi(lat, lon, city_name):
    """Fetch current AQI from WAQI API"""
    if not WAQI_API_KEY:
        return None
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            return None

        aqi_data = data["data"]
        iaqi = aqi_data.get("iaqi", {})

        aqi = aqi_data.get("aqi", 0)
        if isinstance(aqi, str):
            aqi = 0

        return {
            "aqi": int(aqi),
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "source": "WAQI",
            "category": get_aqi_category(int(aqi)),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.warning("WAQI error for %s: %s", city_name, e)
        return None


# ============ MAIN COLLECTOR ============
def collect_all_data():
    """Collect data from all APIs for all cities"""
    all_data = []

    logger.info("=" * 60)
    logger.info("  Multi-API AQI Data Collection")

    for city in CITIES:
        city_data = []
        name = city["name"]
        lat, lon = city["lat"], city["lon"]

        # Try Ambee
        ambee_data = fetch_from_ambee(lat, lon, name)
        if ambee_data and ambee_data["aqi"] > 0:
            city_data.append(ambee_data)
            logger.info("  %s Ambee: AQI=%s, PM2.5=%s", name, ambee_data['aqi'], ambee_data['pm25'])

        time.sleep(0.3)

        # Try WAQI
        waqi_data = fetch_from_waqi(lat, lon, name)
        if waqi_data and waqi_data["aqi"] > 0:
            city_data.append(waqi_data)
            logger.info("  %s WAQI:  AQI=%s, PM2.5=%s", name, waqi_data['aqi'], waqi_data['pm25'])

        time.sleep(0.3)

        # Save all valid data
        for data in city_data:
            save_data(data)
            all_data.append(data)

    logger.info("[TOTAL] Collected %s data points from %s cities", len(all_data), len(CITIES))
    return all_data


def train_with_multi_api():
    """Main function: collect data and train model"""
    logger.info("GA-KELM Training with Multi-API Data")

    # Collect data
    all_data = collect_all_data()

    if len(all_data) < 20:
        logger.warning("Not enough new data, will use existing database records")

    # Train
    logger.info("Training GA-KELM model...")
    result = train_model(all_data)

    # Results
    logger.info("Training Results")
    model = get_model()
    if model.is_trained:
        logger.info("  Status: TRAINED")
        logger.info("  R2 Score: %.4f (%.1f%% accuracy)", model.training_r2, model.training_r2 * 100)
        logger.info("  RMSE: %.4f", model.training_rmse)
        logger.info("  Data Points: %s", model.data_count)
        logger.info("  Optimal C: %.4f", model.best_params.get('C', 0))
        logger.info("  Optimal Gamma: %.6f", model.best_params.get('gamma', 0))
    else:
        logger.info("  Status: NOT TRAINED")

    logger.info("Training complete!")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_with_multi_api()
