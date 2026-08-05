"""
Generate sample training data and train the GA-KELM model
"""
import numpy as np
from model import train_model, get_model_info
from database import save_data
from datetime import datetime, timedelta
import random

# Generate realistic AQI training data
def generate_training_data(num_samples=50):
    """Generate realistic AQI data points"""
    data_list = []
    
    base_time = datetime.now() - timedelta(hours=num_samples * 0.25)
    
    for i in range(num_samples):
        # Generate realistic pollutant values
        pm25 = random.uniform(20, 200)  # PM2.5 range
        pm10 = pm25 * random.uniform(1.1, 1.8)  # PM10 typically higher than PM2.5
        no2 = random.uniform(5, 80)
        o3 = random.uniform(20, 150)
        so2 = random.uniform(2, 30)
        co = random.uniform(0.2, 1.5)
        
        # Calculate realistic AQI based on PM2.5 (EPA formula)
        if pm25 <= 12:
            aqi = (50/12) * pm25
        elif pm25 <= 35.4:
            aqi = 50 + ((100-50)/(35.4-12.1)) * (pm25 - 12.1)
        elif pm25 <= 55.4:
            aqi = 100 + ((150-100)/(55.4-35.5)) * (pm25 - 35.5)
        elif pm25 <= 150.4:
            aqi = 150 + ((200-150)/(150.4-55.5)) * (pm25 - 55.5)
        elif pm25 <= 250.4:
            aqi = 200 + ((300-200)/(250.4-150.5)) * (pm25 - 150.5)
        else:
            aqi = 300 + ((500-300)/(500.4-250.5)) * (pm25 - 250.5)
        
        # Add some noise
        aqi = aqi * random.uniform(0.95, 1.05)
        aqi = max(0, min(500, round(aqi)))
        
        # Get category
        if aqi <= 50:
            category = "Good"
        elif aqi <= 100:
            category = "Moderate"
        elif aqi <= 150:
            category = "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            category = "Unhealthy"
        elif aqi <= 300:
            category = "Very Unhealthy"
        else:
            category = "Hazardous"
        
        timestamp = base_time + timedelta(hours=i * 0.25)
        
        data = {
            "pm25": round(pm25, 2),
            "pm10": round(pm10, 2),
            "no2": round(no2, 2),
            "o3": round(o3, 2),
            "so2": round(so2, 2),
            "co": round(co, 3),
            "aqi": aqi,
            "category": category,
            "latitude": 15.5057,
            "longitude": 80.0499,
            "source": "Training Data",
            "timestamp": timestamp.isoformat()
        }
        
        data_list.append(data)
        
        # Save to database
        save_data(data)
        print(f"Saved data point {i+1}: AQI={aqi}, PM2.5={pm25:.1f}")
    
    return data_list


if __name__ == "__main__":
    print("=" * 50)
    print("[DNA] GA-KELM Model Training")
    print("=" * 50)
    
    # Generate training data
    print("\n[DATA] Generating training data...")
    data_list = generate_training_data(50)
    print(f"\n[OK] Generated {len(data_list)} data points")
    
    # Train the model
    print("\n[TRAIN] Training GA-KELM model...")
    result = train_model(data_list)
    
    print("\n" + "=" * 50)
    print("[RESULT] Training Result:")
    print(result)
    
    # Get model info
    print("\n[INFO] Model Info:")
    info = get_model_info()
    print(info)
    
    print("\n[DONE] Model training complete!")
