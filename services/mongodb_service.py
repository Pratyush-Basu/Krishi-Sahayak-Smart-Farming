"""
services/mongodb_service.py — MongoDB persistence for prediction history.

Uses a single MongoClient connected to local MongoDB Compass.
If MongoDB is unavailable, errors are logged and predictions still succeed.
"""

import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from models.crop_prediction import build_crop_prediction
from models.fertilizer_prediction import build_fertilizer_prediction
from models.disease_prediction import build_disease_prediction

logger = logging.getLogger(__name__)

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
db = client["krishi_sahayak"]


def save_crop_prediction(
    user_id,
    nitrogen,
    phosphorus,
    potassium,
    temperature,
    humidity,
    ph,
    rainfall,
    predicted_crop,
    confidence,
):
    """Save a crop prediction to the crop_predictions collection."""
    try:
        doc = build_crop_prediction(
            user_id=user_id,
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            temperature=temperature,
            humidity=humidity,
            ph=ph,
            rainfall=rainfall,
            predicted_crop=predicted_crop,
            confidence=confidence,
        )
        db.crop_predictions.insert_one(doc)
    except PyMongoError as e:
        logger.error("MongoDB save_crop_prediction failed: %s", e)
    except Exception as e:
        logger.error("Unexpected error in save_crop_prediction: %s", e)


def save_fertilizer_prediction(
    user_id,
    crop_type,
    land_area_acre,
    nitrogen,
    phosphorus,
    potassium,
    language,
    fertilizer,
    ai_explanation="",
):
    """Save a fertilizer prediction to the fertilizer_predictions collection."""
    try:
        doc = build_fertilizer_prediction(
            user_id=user_id,
            crop_type=crop_type,
            land_area_acre=land_area_acre,
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            language=language,
            fertilizer=fertilizer,
            ai_explanation=ai_explanation,
        )
        db.fertilizer_predictions.insert_one(doc)
    except PyMongoError as e:
        logger.error("MongoDB save_fertilizer_prediction failed: %s", e)
    except Exception as e:
        logger.error("Unexpected error in save_fertilizer_prediction: %s", e)


def save_disease_prediction(
    user_id,
    image_name,
    disease_name,
    confidence,
    treatment_summary,
    treatment_details,
):
    """Save a disease prediction to the disease_predictions collection."""
    try:
        doc = build_disease_prediction(
            user_id=user_id,
            image_name=image_name,
            disease_name=disease_name,
            confidence=confidence,
            treatment_summary=treatment_summary,
            treatment_details=treatment_details,
        )
        db.disease_predictions.insert_one(doc)
    except PyMongoError as e:
        logger.error("MongoDB save_disease_prediction failed: %s", e)
    except Exception as e:
        logger.error("Unexpected error in save_disease_prediction: %s", e)


def get_crop_predictions(user_id):
    """Fetch crop predictions for a user, newest first."""
    try:
        return list(
            db.crop_predictions.find({"user_id": user_id}).sort("created_at", -1)
        )
    except PyMongoError as e:
        logger.error("MongoDB get_crop_predictions failed: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error in get_crop_predictions: %s", e)
        return []


def get_fertilizer_predictions(user_id):
    """Fetch fertilizer predictions for a user, newest first."""
    try:
        return list(
            db.fertilizer_predictions.find({"user_id": user_id}).sort("created_at", -1)
        )
    except PyMongoError as e:
        logger.error("MongoDB get_fertilizer_predictions failed: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error in get_fertilizer_predictions: %s", e)
        return []


def get_disease_predictions(user_id):
    """Fetch disease predictions for a user, newest first."""
    try:
        return list(
            db.disease_predictions.find({"user_id": user_id}).sort("created_at", -1)
        )
    except PyMongoError as e:
        logger.error("MongoDB get_disease_predictions failed: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error in get_disease_predictions: %s", e)
        return []
