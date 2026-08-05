"""
Database Module - Firebase Realtime Database / In-Memory Fallback
Real-Time AQI Prediction System

Firebase is used when configured; an in-memory mock database is used otherwise.
"""

import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Firebase Configuration
FIREBASE_URL = os.getenv("FIREBASE_URL")
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "firebase-credentials.json")

# Cache for Firebase init check (0 = not tried, 1 = success, -1 = failed)
_firebase_status = 0


def _try_init_firebase():
    """Attempt Firebase initialization once; cache result."""
    global _firebase_status

    if _firebase_status != 0:
        return _firebase_status == 1

    # Determine if we have the necessary configuration
    cred_obj = None
    if not FIREBASE_URL:
        logger.warning("FIREBASE_URL is not set; using in-memory database")
        _firebase_status = -1
        return False

    try:
        if os.path.exists(FIREBASE_CRED_PATH):
            cred_obj = credentials.Certificate(FIREBASE_CRED_PATH)
        else:
            cred_json = os.getenv("FIREBASE_CREDENTIALS")
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred_obj = credentials.Certificate(cred_dict)

        if cred_obj is None:
            logger.warning("No Firebase credentials found; using in-memory database")
            _firebase_status = -1
            return False

        # Avoid double-init
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred_obj, {'databaseURL': FIREBASE_URL})

        _firebase_status = 1
        logger.info("Firebase connected successfully")
        return True

    except Exception as e:
        logger.exception("Firebase connection failed: %s", e)
        _firebase_status = -1
        return False


def get_ref(path: str):
    """Get a Firebase database reference, or None if Firebase is unavailable."""
    if not _try_init_firebase():
        return None
    return db.reference(path)


# ============ AQI Records ============

def save_data(data: dict) -> str:
    """Save AQI data to Firebase"""
    try:
        ref = get_ref('records')
        if ref is None:
            return MockDatabase.save_data(data)
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        
        # Push creates a unique key
        new_ref = ref.push(data)
        
        logger.info("Data saved with key: %s", new_ref.key)
        return new_ref.key
        
    except Exception as e:
        logger.exception("Error saving data: %s", e)
        return None


def get_latest_data() -> dict:
    """Get the most recent AQI reading"""
    try:
        ref = get_ref('records')
        if ref is None:
            return MockDatabase.get_latest_data()
        
        # Query last record ordered by timestamp
        snapshot = ref.order_by_child('timestamp').limit_to_last(1).get()
        
        if snapshot:
            for key, value in snapshot.items():
                value['_id'] = key
                return value
        
        return None
        
    except Exception as e:
        logger.exception("Error getting latest data: %s", e)
        return None


def get_historical_data(limit: int = 100) -> list:
    """Get historical AQI readings"""
    try:
        limit = max(1, min(int(limit), 1000))
        ref = get_ref('records')
        if ref is None:
            return MockDatabase.get_historical_data(limit)
        
        # Get all records (no ordering to avoid index requirement)
        snapshot = ref.get()
        
        if not snapshot:
            return []
        
        # Convert to list and add keys
        records = []
        for key, value in snapshot.items():
            if isinstance(value, dict):
                value['_id'] = key
                records.append(value)
        
        # Sort by timestamp descending in Python
        records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return only the requested limit
        return records[:limit]
        
    except Exception as e:
        logger.exception("Error getting historical data: %s", e)
        return []


def get_training_data() -> list:
    """Get data for model training"""
    return get_historical_data(500)


# ============ Predictions ============

def save_prediction(prediction: dict) -> str:
    """Save a prediction to Firebase"""
    try:
        ref = get_ref('predictions')
        if ref is None:
            return MockDatabase.save_prediction(prediction)
        
        prediction['created_at'] = datetime.now().isoformat()
        new_ref = ref.push(prediction)
        
        return new_ref.key
        
    except Exception as e:
        logger.exception("Error saving prediction: %s", e)
        return None


def get_predictions(limit: int = 24) -> list:
    """Get recent predictions"""
    try:
        limit = max(1, min(int(limit), 1000))
        ref = get_ref('predictions')
        if ref is None:
            return MockDatabase.get_predictions(limit)
        
        snapshot = ref.order_by_child('created_at').limit_to_last(limit).get()
        
        if not snapshot:
            return []
        
        predictions = []
        for key, value in snapshot.items():
            value['_id'] = key
            predictions.append(value)
        
        predictions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return predictions
        
    except Exception as e:
        logger.exception("Error getting predictions: %s", e)
        return []


# ============ Model Info ============

def save_model_info(model_info: dict) -> str:
    """Save trained model metadata"""
    try:
        ref = get_ref('models')
        if ref is None:
            return None
        
        model_info['trained_at'] = datetime.now().isoformat()
        new_ref = ref.push(model_info)
        
        return new_ref.key
        
    except Exception as e:
        logger.exception("Error saving model info: %s", e)
        return None


def get_latest_model() -> dict:
    """Get the most recent model info"""
    try:
        ref = get_ref('models')
        if ref is None:
            return None
        
        snapshot = ref.order_by_child('trained_at').limit_to_last(1).get()
        
        if snapshot:
            for key, value in snapshot.items():
                value['_id'] = key
                return value
        
        return None
        
    except Exception as e:
        logger.exception("Error getting latest model: %s", e)
        return None


# ============ Test Connection ============

def test_connection() -> bool:
    """Test Firebase connection"""
    try:
        if _try_init_firebase():
            # Try a simple read
            ref = get_ref('/')
            if ref is not None:
                ref.get()
                logger.info("Firebase connection test passed")
                return True
        return False
    except Exception as e:
        logger.exception("Firebase connection test failed: %s", e)
        return False


# ============ Mock Mode (for demo without Firebase) ============

_mock_data = {
    'records': [],
    'predictions': [],
    'models': []
}

class MockDatabase:
    """Mock database for demo/testing without Firebase"""
    
    @staticmethod
    def save_data(data: dict) -> str:
        data['_id'] = f"mock_{len(_mock_data['records'])}"
        data['timestamp'] = datetime.now().isoformat()
        _mock_data['records'].insert(0, data)
        return data['_id']
    
    @staticmethod
    def get_latest_data() -> dict:
        return _mock_data['records'][0] if _mock_data['records'] else None
    
    @staticmethod
    def get_historical_data(limit: int = 100) -> list:
        return _mock_data['records'][:limit]
    
    @staticmethod
    def save_prediction(prediction: dict) -> str:
        prediction['_id'] = f"pred_{len(_mock_data['predictions'])}"
        prediction['created_at'] = datetime.now().isoformat()
        _mock_data['predictions'].insert(0, prediction)
        return prediction['_id']
    
    @staticmethod
    def get_predictions(limit: int = 24) -> list:
        return _mock_data['predictions'][:limit]


# Use mock if Firebase not configured
if not FIREBASE_URL:
    logger.info("Firebase not configured; using in-memory database")


# Test
if __name__ == "__main__":
    logger.info("Testing database")
    test_connection()
