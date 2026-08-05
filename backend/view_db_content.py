import os
import json
from database import get_latest_data, get_historical_data, test_connection

def view_database():
    print("--- Firebase Connection Test ---")
    connected = test_connection()
    print(f"Connection Status: {'SUCCESS' if connected else 'FAILED'}")
    
    print("\n--- Latest AQI Record ---")
    latest = get_latest_data()
    if latest:
        print(json.dumps(latest, indent=2))
    else:
        print("No records found.")
        
    print("\n--- Historical Data (Top 5) ---")
    history = get_historical_data(limit=5)
    if history:
        for idx, rec in enumerate(history):
            print(f"{idx+1}. Time: {rec.get('timestamp')} | AQI: {rec.get('aqi')}")
    else:
        print("No historical data found.")

if __name__ == "__main__":
    view_database()
