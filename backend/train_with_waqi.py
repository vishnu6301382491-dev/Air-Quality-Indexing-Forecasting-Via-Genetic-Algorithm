"""
Fetch real AQI data from WAQI API and train GA-KELM model
Uses World Air Quality Index (aqicn.org) API for real data
"""
import requests
import time
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from model import train_model, get_model_info
from database import save_data

load_dotenv()
logger = logging.getLogger(__name__)

# WAQI API Token
WAQI_TOKEN = os.getenv("WAQI_API_KEY")
WAQI_BASE_URL = "https://api.waqi.info"

# Indian cities to fetch data from
CITIES = [
    "ongole", "visakhapatnam", "hyderabad", "vijayawada", "chennai",
    "bangalore", "mumbai", "delhi", "kolkata", "pune", "ahmedabad",
    "jaipur", "lucknow", "kanpur", "nagpur", "patna", "indore",
    "bhopal", "coimbatore", "kochi"
]


def fetch_city_aqi(city: str) -> dict:
    """Fetch current AQI data from WAQI for a city"""
    if not WAQI_TOKEN:
        return None
    try:
        url = f"{WAQI_BASE_URL}/feed/{city}/?token={WAQI_TOKEN}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            logger.info("  [SKIP] %s: %s", city, data.get('data', 'Unknown error'))
            return None

        aqi_data = data["data"]
        iaqi = aqi_data.get("iaqi", {})

        result = {
            "aqi": aqi_data.get("aqi", 0),
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "city": aqi_data.get("city", {}).get("name", city),
            "latitude": aqi_data.get("city", {}).get("geo", [0, 0])[0],
            "longitude": aqi_data.get("city", {}).get("geo", [0, 0])[1],
            "source": "WAQI",
            "timestamp": datetime.now().isoformat()
        }

        aqi = result["aqi"]
        if isinstance(aqi, str) and aqi == "-":
            return None

        aqi = int(aqi) if aqi else 0
        result["aqi"] = aqi

        if aqi <= 50:
            result["category"] = "Good"
        elif aqi <= 100:
            result["category"] = "Moderate"
        elif aqi <= 150:
            result["category"] = "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            result["category"] = "Unhealthy"
        elif aqi <= 300:
            result["category"] = "Very Unhealthy"
        else:
            result["category"] = "Hazardous"

        return result

    except Exception as e:
        logger.warning("  [ERROR] %s: %s", city, e)
        return None


def fetch_all_cities_data():
    """Fetch AQI data from multiple cities"""
    all_data = []
    logger.info("[FETCH] Fetching real AQI data from WAQI API...")

    for city in CITIES:
        result = fetch_city_aqi(city)
        if result and result["aqi"] > 0 and result["pm25"] > 0:
            all_data.append(result)
            save_data(result)
            logger.info("  [OK] %s: AQI=%s, PM2.5=%s", city, result['aqi'], result['pm25'])
        time.sleep(0.5)

    logger.info("[DONE] Fetched %s valid data points", len(all_data))
    return all_data


def train_with_real_data():
    """Fetch real data and train the model"""
    logger.info("GA-KELM Model Training with Real WAQI Data")

    data_list = fetch_all_cities_data()

    if len(data_list) < 10:
        logger.warning("Not enough data for training. Fetching more...")
        additional_cities = [
            "tirupati", "guntur", "nellore", "rajahmundry", "kakinada",
            "warangal", "karimnagar", "nizamabad", "khammam", "mahabubnagar",
            "kurnool", "kadapa", "anantapur", "chittoor", "srikakulam"
        ]
        for city in additional_cities:
            result = fetch_city_aqi(city)
            if result and result["aqi"] > 0:
                data_list.append(result)
                save_data(result)
                logger.info("  [OK] %s: AQI=%s", city, result['aqi'])
            time.sleep(0.5)

    logger.info("[DATA] Total data points: %s", len(data_list))

    if len(data_list) < 20:
        logger.error("Still not enough data points (need 20+)")
        logger.error("The WAQI API may not have data for some cities.")
        return None

    logger.info("[TRAIN] Training GA-KELM model with real data...")
    result = train_model(data_list)

    logger.info("Training Result")
    for key, value in result.items():
        logger.info("  %s: %s", key, value)

    logger.info("Model Info:")
    info = get_model_info()
    for key, value in info.items():
        logger.info("  %s: %s", key, value)

    logger.info("[SUCCESS] Model trained with real WAQI data!")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_with_real_data()
