"""
Data Fetcher Module - Multi-Source AQI API
Uses WAQI (primary), Ambee (secondary), OpenWeatherMap (fallback)
Real-Time AQI Prediction System
"""

import requests
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from utils import finite_number, get_aqi_category, valid_coordinates, calculate_aqi_from_pm25

logger = logging.getLogger(__name__)

load_dotenv()

# API Keys
OPENWEATHERMAP_KEY = os.getenv("API_KEY")
WAQI_API_KEY = os.getenv("WAQI_API_KEY")
AMBEE_API_KEY = os.getenv("AMBEE_API_KEY")

LATITUDE = float(os.getenv("LATITUDE", "15.5057"))  # Ongole default
LONGITUDE = float(os.getenv("LONGITUDE", "80.0499"))


def fetch_from_waqi(lat: float, lon: float):
    """Fetch AQI from WAQI API (primary source - most accurate)"""
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict) or data.get("status") != "ok" or not isinstance(data.get('data'), dict):
            logger.warning("WAQI returned an unsuccessful response: %s", data.get('data', 'Unknown') if isinstance(data, dict) else 'invalid body')
            return None
        
        aqi_data = data["data"]
        iaqi = aqi_data.get("iaqi", {})
        
        aqi = aqi_data.get("aqi", 0)
        if isinstance(aqi, str) and aqi == "-":
            return None
        aqi = int(aqi) if aqi else 0
        
        # Get station name
        city_info = aqi_data.get("city", {})
        station_name = city_info.get("name", "Unknown")
        
        result = {
            "aqi": aqi,
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "category": get_aqi_category(aqi),
            "station": station_name,
            "source": "WAQI",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("WAQI %s: AQI=%s, PM2.5=%s", station_name, aqi, result['pm25'])
        return result
        
    except Exception as e:
        logger.warning("WAQI request failed: %s", e)
        return None


def fetch_from_ambee(lat: float, lon: float):
    """Fetch AQI from Ambee API (secondary source)"""
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
        aqi = station.get("AQI", 0)
        
        result = {
            "aqi": aqi,
            "pm25": station.get("PM25", 0),
            "pm10": station.get("PM10", 0),
            "no2": station.get("NO2", 0),
            "o3": station.get("OZONE", 0),
            "so2": station.get("SO2", 0),
            "co": station.get("CO", 0),
            "category": get_aqi_category(aqi),
            "station": station.get("stationName", "Ambee Station"),
            "source": "Ambee",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Ambee AQI=%s, PM2.5=%s", aqi, result['pm25'])
        return result
        
    except Exception as e:
        logger.warning("Ambee request failed: %s", e)
        return None


def fetch_from_openweathermap(lat: float, lon: float):
    """Fetch AQI from OpenWeatherMap (fallback)"""
    if not OPENWEATHERMAP_KEY:
        return None
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "list" not in data or len(data["list"]) == 0:
            return None
        
        pollution = data["list"][0]
        components = pollution.get("components", {})
        
        pm25 = components.get("pm2_5", 0)
        
        # Calculate EPA AQI from PM2.5 using shared utility
        aqi = calculate_aqi_from_pm25(pm25)
        
        result = {
            "aqi": aqi,
            "pm25": round(pm25, 2),
            "pm10": round(components.get("pm10", 0), 2),
            "no2": round(components.get("no2", 0), 2),
            "o3": round(components.get("o3", 0), 2),
            "so2": round(components.get("so2", 0), 2),
            "co": round(components.get("co", 0) / 1000, 3),
            "category": get_aqi_category(aqi),
            "station": "OpenWeatherMap",
            "source": "OpenWeatherMap",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("OWM AQI=%s, PM2.5=%s", aqi, pm25)
        return result
        
    except Exception as e:
        logger.warning("OWM AQI request failed: %s", e)
        return None


def fetch_weather(lat: float = None, lon: float = None):
    """Fetch weather data from The Weather Company API (primary) or OpenWeatherMap (fallback)"""
    lat = LATITUDE if lat is None else lat
    lon = LONGITUDE if lon is None else lon
    
    # Try The Weather Company API first
    TWC_API_KEY = os.getenv("TWC_API_KEY")
    
    if TWC_API_KEY:
        try:
            url = f"https://api.weather.com/v3/wx/observations/current?geocode={lat},{lon}&units=m&language=en-US&format=json&apiKey={TWC_API_KEY}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info("Weather fetched from TWC")
                return {
                    "temperature": data.get("temperature", 25),
                    "feels_like": data.get("temperatureFeelsLike", 25),
                    "humidity": data.get("relativeHumidity", 60),
                    "pressure": data.get("pressureMeanSeaLevel", 1013),
                    "wind_speed": round((data.get("windSpeed", 0) or 0), 1),
                    "wind_deg": data.get("windDirection", 0) or 0,
                    "weather": data.get("wxPhraseLong", "Clear"),
                    "weather_desc": data.get("wxPhraseLong", "clear sky"),
                    "weather_icon": data.get("iconCode", 32),
                    "clouds": data.get("cloudCover", 0) or 0,
                    "visibility": round((data.get("visibility", 10) or 10), 1),
                    "uv_index": data.get("uvIndex", 0) or 0
                }
        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            logger.warning("TWC request failed: %s", e)
    
    # Fallback to OpenWeatherMap
    if not OPENWEATHERMAP_KEY:
        return _get_mock_weather()
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": round(data["wind"]["speed"] * 3.6, 1),
            "wind_deg": data["wind"].get("deg", 0),
            "weather": data["weather"][0]["main"],
            "weather_desc": data["weather"][0]["description"],
            "weather_icon": data["weather"][0]["icon"],
            "clouds": data["clouds"]["all"],
            "visibility": data.get("visibility", 10000) / 1000,
            "uv_index": 0
        }
    except Exception as e:
        logger.warning("OWM weather request failed: %s", e)
        return _get_mock_weather()


def _get_mock_weather():
    """Mock weather data"""
    import random
    return {
        "temperature": 25,
        "feels_like": 27,
        "humidity": 63,
        "pressure": 1012,
        "wind_speed": 14,
        "wind_deg": 180,
        "weather": "Sunny",
        "weather_desc": "clear sky",
        "weather_icon": "01d",
        "clouds": 20,
        "visibility": 10.0,
        "uv_index": 5
    }


def fetch_data(lat: float = None, lon: float = None):
    """
    Fetch real-time AQI data from multiple sources
    Priority: WAQI > Ambee > OpenWeatherMap
    """
    lat = LATITUDE if lat is None else lat
    lon = LONGITUDE if lon is None else lon

    if not valid_coordinates(lat, lon):
        raise ValueError('Latitude must be between -90 and 90 and longitude between -180 and 180')
    
    logger.info("Fetching AQI for (%s, %s)", lat, lon)
    
    # Try WAQI first (most accurate, matches IQAir/AQI.in data)
    result = fetch_from_waqi(lat, lon)
    
    # If WAQI fails, try Ambee
    if not result or result.get("aqi", 0) == 0:
        result = fetch_from_ambee(lat, lon)
    
    # If Ambee fails, try OpenWeatherMap
    if not result or result.get("aqi", 0) == 0:
        result = fetch_from_openweathermap(lat, lon)
    
    # If all fail, return mock data
    if not result:
        logger.warning("All AQI APIs failed; using fallback data")
        result = {
            "aqi": 150,
            "pm25": 55,
            "pm10": 80,
            "no2": 30,
            "o3": 50,
            "so2": 10,
            "co": 0.5,
            "category": "Unhealthy for Sensitive Groups",
            "station": "Fallback",
            "source": "Fallback",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
    
    # Add weather data
    result["weather"] = fetch_weather(lat, lon)
    
    return result

if __name__ == "__main__":
    # Test with Ongole coordinates
    logger.info("Testing data fetch")
    data = fetch_data(15.5057, 80.0499)
    logger.info("Result: AQI=%s, Category=%s, PM2.5=%s, Station=%s", data['aqi'], data['category'], data['pm25'], data.get('station', 'N/A'))
