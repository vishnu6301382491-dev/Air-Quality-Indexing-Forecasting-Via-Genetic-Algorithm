"""
Scheduler Module - Background Tasks
Real-Time AQI Prediction System

Handles:
- Periodic AQI data fetching
- Automatic model retraining
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import threading
import logging

from data_fetch import fetch_data
from database import save_data, get_training_data, save_model_info, save_prediction
from model import train_model, predict_from_data, get_model
from utils import get_aqi_category

logger = logging.getLogger(__name__)


class AQIScheduler:
    """
    Background scheduler for automated tasks.

    If a single task run fails, the scheduler continues running future
    executions (APScheduler default behaviour with ``BackgroundScheduler``).
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self._lock = threading.Lock()

    def _fetch_and_save(self):
        """Fetch AQI data, save it, and make a prediction."""
        try:
            logger.info("Fetching AQI data")
            data = fetch_data()

            if data:
                save_data(data)
                logger.info("Data saved: AQI=%s", data.get('aqi'))

                # Also make and save prediction
                model = get_model()
                predicted = None
                if model.is_trained:
                    predicted = predict_from_data(data)
                else:
                    # Fallback: use current AQI or EPA formula
                    from utils import calculate_aqi_from_pm25
                    pm25 = data.get('pm25')
                    if pm25:
                        predicted = calculate_aqi_from_pm25(pm25)
                    else:
                        predicted = data.get('aqi', 0)

                if predicted is not None:
                    category = get_aqi_category(int(predicted))
                    pred_record = {
                        "predicted_aqi": float(predicted),
                        "category": category,
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude")
                    }
                    save_prediction(pred_record)
                    logger.info("Prediction saved: %s (%s)", round(predicted, 1), category)

        except Exception as e:
            logger.exception("Fetch task failed: %s", e)

    def _retrain_model(self):
        """Retrain the GA-KELM model with latest data."""
        try:
            logger.info("Starting model retraining")

            # Get training data from database
            data_list = get_training_data()

            if len(data_list) < 20:
                logger.warning("Not enough data for training (have %s, need 20+)", len(data_list))
                return

            # Train model
            result = train_model(data_list)

            if result and result.get('status') == 'success':
                save_model_info(result)
                logger.info("Model retrained successfully")
            else:
                logger.warning("Model retraining did not complete: %s", result)

        except Exception as e:
            logger.exception("Training task failed: %s", e)

    def start(self):
        """Start the scheduler."""
        if self.is_running:
            return

        # Fetch data every 15 minutes
        self.scheduler.add_job(
            self._fetch_and_save,
            trigger=IntervalTrigger(minutes=15),
            id='fetch_aqi_data',
            name='Fetch AQI Data',
            replace_existing=True,
            max_instances=1  # Never overlap runs
        )

        # Retrain model every 24 hours
        self.scheduler.add_job(
            self._retrain_model,
            trigger=IntervalTrigger(hours=24),
            id='retrain_model',
            name='Retrain GA-KELM Model',
            replace_existing=True,
            max_instances=1
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started")

        # Run initial fetch
        self._fetch_and_save()

    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler stopped")

    def trigger_fetch(self):
        """Manually trigger data fetch."""
        self._fetch_and_save()

    def trigger_retrain(self):
        """Manually trigger model retraining."""
        self._retrain_model()


# Global scheduler instance
scheduler = AQIScheduler()


def start_scheduler():
    """Start the global scheduler."""
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    scheduler.stop()


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing Scheduler")
    scheduler.trigger_fetch()
