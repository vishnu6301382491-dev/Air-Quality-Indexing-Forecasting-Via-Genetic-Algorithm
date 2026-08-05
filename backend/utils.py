"""
Shared backend validation and AQI helpers.
Real-Time AQI Prediction System

Central location for:
- Coordinate validation
- EPA AQI calculation
- AQI category labels
- Numeric sanitization
"""

import math
import logging

logger = logging.getLogger(__name__)

# EPA AQI Breakpoints for PM2.5 (for fallback calculation)
AQI_BREAKPOINTS_PM25 = [
    (0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 500.4, 301, 500),
]

AQI_CATEGORIES = (
    (50, 'Good'),
    (100, 'Moderate'),
    (150, 'Unhealthy for Sensitive Groups'),
    (200, 'Unhealthy'),
    (300, 'Very Unhealthy'),
    (math.inf, 'Hazardous'),
)


def finite_number(value, default=0.0, minimum=None):
    """Convert a value to a finite float, returning default on failure."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number) or (minimum is not None and number < minimum):
        return default
    return number


def get_aqi_category(aqi):
    """Return the AQI category label for a given numeric AQI value."""
    value = finite_number(aqi, 0, 0)
    return next(label for maximum, label in AQI_CATEGORIES if value <= maximum)


def valid_coordinates(lat, lon):
    """Validate latitude (-90..90) and longitude (-180..180)."""
    latitude = finite_number(lat, None)
    longitude = finite_number(lon, None)
    if latitude is None or longitude is None:
        return False
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return False
    return True


def calculate_aqi_from_pm25(pm25):
    """Calculate AQI from PM2.5 concentration using EPA formula.

    Uses the standard EPA breakpoints to convert PM2.5 (µg/m³) to AQI.

    Args:
        pm25: PM2.5 concentration in µg/m³.

    Returns:
        Integer AQI value between 0 and 500.
    """
    pm25 = finite_number(pm25, 0)
    if pm25 <= 0:
        return 0
    if pm25 <= 500.4:
        for low_conc, high_conc, low_aqi, high_aqi in AQI_BREAKPOINTS_PM25:
            if low_conc <= pm25 <= high_conc:
                aqi = ((high_aqi - low_aqi) / (high_conc - low_conc)) * (pm25 - low_conc) + low_aqi
                return round(aqi)
    return min(round(pm25), 500) if pm25 > 500 else 0
