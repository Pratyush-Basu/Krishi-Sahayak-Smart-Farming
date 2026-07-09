"""
services/ml_service.py — ModelManager: Load All ML Models Once

Problem with the old approach:
  - Each separate app loaded its model at import time
  - Models were reloaded on every restart
  - Disease model (178 MB Keras) was loaded inside the route handler

Solution — ModelManager:
  - Loads ALL models exactly once at application startup
  - Stores them in memory for the lifetime of the server
  - Routes access models via current_app.extensions['ml']
  - Thread-safe — models are read-only after loading

Models managed:
  1. Crop Recommendation  → crop_model.pkl + crop_le.pkl + ideal_npk.csv
  2. Disease Detection    → disease_model.keras (TensorFlow/Keras)
"""

import os
import logging
import pickle
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Centralized manager for all ML models.

    Usage in app.py:
        ml = ModelManager()
        ml.load_all(app.config)
        app.extensions['ml'] = ml

    Usage in routes:
        from flask import current_app
        ml = current_app.extensions['ml']
        result = ml.predict_crop(features)
    """

    def __init__(self):
        # Crop module
        self.crop_model   = None
        self.crop_le      = None
        self.npk_df       = None

        # Disease module
        self.disease_model = None
        self.disease_class_names = [
            "bell pepper_bacterial spot",
            "bell pepper_healthy",
            "potato_early blight",
            "potato_late blight",
            "potato_healthy",
            "tomato_bacterial spot",
            "tomato_early blight",
            "tomato_late blight",
            "tomato_leaf mold",
            "tomato_septoria leaf spot",
            "tomato_spider mites",
            "tomato_target spot",
            "tomato_yellow leaf curl virus",
            "tomato_mosaic virus",
            "tomato_healthy",
        ]
        self.disease_img_size = 256

        # Crop constants (same as original app.py)
        self.all_crops = [
            "apple", "banana", "blackgram", "chickpea", "coconut", "coffeea",
            "cotton", "grapes", "jute", "kidneybeans", "lentil", "maize",
            "mango", "mothbeans", "mungbean", "muskmelon", "orange",
            "papaya", "pigeonpeas", "pomegranate", "rice", "watermelon",
        ]

        self.mandi_crop_map = {
            "rice": "Rice", "maize": "Maize", "jute": "Jute",
            "cotton": "Cotton", "banana": "Banana", "mango": "Mango",
            "grapes": "Grapes", "watermelon": "Water Melon",
            "muskmelon": "Musk Melon", "papaya": "Papaya",
            "coconut": "Coconut", "orange": "Orange", "lentil": "Lentil",
            "blackgram": "Black Gram", "mungbean": "Green Gram",
            "kidneybeans": "Rajma", "chickpea": "Gram",
            "pigeonpeas": "Arhar (Tur/Red Gram)(Whole)",
            "mothbeans": "Moth", "pomegranate": "Pomegranate",
            "apple": "Apple",
        }

    # ── Loaders ──────────────────────────────────────────────────────

    def load_all(self, config: dict):
        """
        Load all models at startup. Called once from create_app().

        Args:
            config: Flask app.config dict (contains model file paths)
        """
        self._load_crop_model(config)
        self._load_disease_model(config)

    def _load_crop_model(self, config: dict):
        """Load crop recommendation model, label encoder, and NPK CSV."""
        crop_path = config.get("CROP_MODEL_PATH", "trained_models/crop_model.pkl")
        le_path   = config.get("CROP_LE_PATH",    "trained_models/crop_le.pkl")
        npk_path  = config.get("CROP_NPK_CSV",    "trained_models/ideal_npk.csv")

        try:
            if os.path.exists(crop_path) and os.path.exists(le_path):
                with open(crop_path, "rb") as f:
                    self.crop_model = pickle.load(f)
                with open(le_path, "rb") as f:
                    self.crop_le = pickle.load(f)
                logger.info("Crop recommendation model loaded successfully")
            else:
                logger.warning(f"Crop model not found at: {crop_path}")
                logger.warning("Copy from: crop_recommendation_system/model.pkl -> trained_models/crop_model.pkl")

            if os.path.exists(npk_path):
                self.npk_df = pd.read_csv(npk_path)
                self.npk_df["crop"] = self.npk_df["crop"].str.lower()
                logger.info("NPK dataset loaded successfully")
            else:
                logger.warning(f"NPK CSV not found at: {npk_path}")

        except Exception as e:
            logger.error(f"Failed to load crop model: {e}")

    def _load_disease_model(self, config: dict):
        """Load disease detection Keras model (178 MB — takes a moment)."""
        model_path = config.get("DISEASE_MODEL_PATH", "trained_models/disease_model.keras")

        if not os.path.exists(model_path):
            logger.warning(f"Disease model not found at: {model_path}")
            logger.warning("Copy from: plant-disease-detection-system-main/best_model_resume.keras -> trained_models/disease_model.keras")
            return

        try:
            import keras
            self.disease_model = keras.models.load_model(model_path)
            self._keras_module = keras
            logger.info("Disease detection model loaded successfully (standalone keras)")
            return
        except Exception:
            pass

        try:
            import tensorflow as tf
            self.disease_model = tf.keras.models.load_model(model_path)
            self._keras_module = tf.keras
            logger.info("Disease detection model loaded successfully (tf.keras)")
            return
        except Exception as e:
            logger.exception(e)

        # If we get here, model didn't load — disease detection will be disabled
        if self.disease_model is None:
            logger.warning("Disease detection model not loaded — feature disabled. "
                           "Fix: pip install tensorflow==2.15.0 (or compatible version)")

    # ── Prediction Methods ───────────────────────────────────────────

    def predict_crop(self, features: list) -> dict:
        """
        Predict top-5 crops from soil/climate features.

        Args:
            features: list of [N, P, K, temperature, humidity, ph, rainfall]

        Returns:
            dict with 'top_crop', 'labels', 'values' or 'error'
        """
        if self.crop_model is None:
            return {"error": "Crop model not loaded. Check trained_models/ folder."}

        try:
            arr   = np.array(features).reshape(1, -1)
            probs = self.crop_model.predict_proba(arr)[0]
            labels_encoded = self.crop_model.classes_
            class_labels   = self.crop_le.inverse_transform(labels_encoded)

            predictions = sorted(
                zip(class_labels, probs),
                key=lambda x: x[1], reverse=True
            )[:5]

            return {
                "top_crop": predictions[0][0],
                "labels":   [c for c, _ in predictions],
                "values":   [round(p * 100, 2) for _, p in predictions],
            }
        except Exception as e:
            logger.error(f"Crop prediction failed: {e}")
            return {"error": str(e)}

    def recommend_fertilizer(self, crop: str, area: float, soil: dict) -> dict:
        """
        Calculate fertilizer recommendation based on NPK deficiency.

        Args:
            crop: crop name (lowercase)
            area: land area in acres
            soil: dict with N, P, K values

        Returns:
            dict with ideal, deficiency, fertilizer amounts or error
        """
        if self.npk_df is None:
            return {"error": "NPK data not loaded."}

        crop = crop.lower()
        rows = self.npk_df[self.npk_df["crop"] == crop]
        if rows.empty:
            return {"error": f"No NPK data found for crop: {crop}"}

        row   = rows.iloc[0]
        ideal = {"N": row["N"], "P": row["P"], "K": row["K"]}

        deficiency = {
            "N": max(0, ideal["N"] - soil["N"]),
            "P": max(0, ideal["P"] - soil["P"]),
            "K": max(0, ideal["K"] - soil["K"]),
        }

        fertilizer = {}
        if deficiency["N"] > 0:
            fertilizer["Urea (46% N)"] = round((deficiency["N"] / 0.46) * area, 2)
        if deficiency["P"] > 0:
            fertilizer["DAP (46% P)"] = round((deficiency["P"] / 0.46) * area, 2)
        if deficiency["K"] > 0:
            fertilizer["MOP (60% K)"] = round((deficiency["K"] / 0.60) * area, 2)

        return {
            "ideal":      ideal,
            "deficiency": deficiency,
            "fertilizer": fertilizer,
        }

    def predict_disease(self, img_path: str) -> tuple:
        """
        Predict plant disease from a leaf image.

        Args:
            img_path: absolute path to the uploaded image file

        Returns:
            (class_name, confidence_percent) tuple
            e.g. ("tomato_early blight", 94.23)
        """
        if self.disease_model is None:
            return None, None

        try:
            # Use the keras module that was used to load the model
            keras_module = getattr(self, '_keras_module', None)
            if keras_module is None:
                try:
                    import keras
                    keras_module = keras
                except ImportError:
                    import tensorflow as tf
                    keras_module = tf.keras

            model_input_shape = getattr(self.disease_model, "input_shape", None)
            expected_size = self.disease_img_size
            if model_input_shape and len(model_input_shape) >= 3 and model_input_shape[1] is not None:
                expected_size = int(model_input_shape[1])

            img = keras_module.preprocessing.image.load_img(
                img_path, target_size=(expected_size, expected_size), color_mode="rgb"
            )
            img_array = keras_module.preprocessing.image.img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            preds = self.disease_model.predict(img_array, verbose=0)
            output_classes = int(preds.shape[1]) if len(preds.shape) == 2 else None
            if output_classes is None:
                raise ValueError(f"Unexpected prediction tensor shape: {preds.shape}")
            if output_classes != len(self.disease_class_names):
                raise ValueError(
                    f"Class count mismatch: model outputs {output_classes}, "
                    f"class_names has {len(self.disease_class_names)}"
                )
            class_idx = int(np.argmax(preds))
            confidence = round(float(preds[0][class_idx]) * 100, 2)
            class_name = self.disease_class_names[class_idx] if class_idx < len(self.disease_class_names) else None

            return class_name, confidence

        except Exception:
            logger.exception("Disease prediction failed")
            return None, None
