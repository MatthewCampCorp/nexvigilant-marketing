"""
Lead Scoring Prediction API
Real-time lead scoring endpoint deployed on Cloud Run

Endpoint: POST /predict
Input: Lead features (JSON)
Output: Lead score 0-100 + confidence

Author: Data Science Team
Last Updated: 2025-10-23
"""

import os
import json
import logging
from typing import Dict, List
from datetime import datetime

import pandas as pd
import xgboost as xgb
from flask import Flask, request, jsonify
from google.cloud import bigquery, secretmanager
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables
MODEL = None
FEATURE_NAMES = None
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'nexvigilant-marketing-prod')
MODEL_VERSION = os.getenv('MODEL_VERSION', 'v1')


def load_model(model_path: str = 'models/lead_scoring_v1.json'):
    """Load trained XGBoost model"""
    global MODEL, FEATURE_NAMES

    logger.info(f"Loading model from {model_path}")

    # Load XGBoost model
    MODEL = xgb.XGBClassifier()
    MODEL.load_model(model_path)

    # Load feature names
    feature_names_path = model_path.replace('.json', '_features.json')
    with open(feature_names_path, 'r') as f:
        metadata = json.load(f)
        FEATURE_NAMES = metadata['feature_names']

    logger.info(f"Model loaded successfully: {len(FEATURE_NAMES)} features")


def preprocess_input(lead_data: Dict) -> pd.DataFrame:
    """
    Preprocess lead data for prediction

    Args:
        lead_data: Dictionary with lead features

    Returns:
        DataFrame with processed features
    """
    # Default values for missing features
    defaults = {
        # Demographics
        'industry': 'Unknown',
        'company_size_bucket': 'Unknown',
        'title_level': 'Unknown',
        'country': 'Unknown',
        'account_age_days': 0,

        # Behavioral
        'page_views_7d': 0,
        'page_views_30d': 0,
        'unique_pages_7d': 0,
        'visits_7d': 0,
        'visits_30d': 0,
        'avg_session_duration_7d': 0,
        'email_opens_7d': 0,
        'email_opens_30d': 0,
        'email_clicks_7d': 0,
        'email_clicks_30d': 0,
        'content_downloads_30d': 0,
        'days_since_last_visit': 999,
        'days_since_last_email_open': 999,

        # Engagement
        'engagement_score': 0,
        'recency_score': 0,
        'frequency_score': 0,
        'monetary_score': 0,
        'rfm_segment': 'Unknown',

        # Financial
        'total_revenue': 0,
        'revenue_30d': 0,
        'revenue_90d': 0,
        'average_order_value': 0,
        'total_orders': 0,
        'orders_30d': 0,
        'days_since_last_purchase': 999,
        'lifetime_value': 0
    }

    # Merge with defaults
    for key, default_value in defaults.items():
        if key not in lead_data:
            lead_data[key] = default_value

    # Create DataFrame
    df = pd.DataFrame([lead_data])

    # One-hot encode categorical variables (same as training)
    categorical_cols = ['industry', 'company_size_bucket', 'title_level', 'country', 'rfm_segment']
    df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

    # Ensure all training features are present
    for feature in FEATURE_NAMES:
        if feature not in df.columns:
            df[feature] = 0

    # Select only training features in correct order
    df = df[FEATURE_NAMES]

    return df


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': MODEL is not None,
        'model_version': MODEL_VERSION,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict lead score

    Request body:
    {
        "lead_id": "lead_12345",
        "email": "john@company.com",
        "industry": "Technology",
        "page_views_30d": 25,
        "email_opens_30d": 10,
        ...
    }

    Response:
    {
        "lead_id": "lead_12345",
        "lead_score": 85,
        "conversion_probability": 0.85,
        "confidence": "high",
        "grade": "A",
        "predicted_at": "2025-10-23T10:30:00",
        "model_version": "v1"
    }
    """
    try:
        # Parse request
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        lead_id = data.get('lead_id', 'unknown')

        # Preprocess
        X = preprocess_input(data)

        # Predict
        probability = MODEL.predict_proba(X)[0, 1]
        lead_score = int(probability * 100)

        # Calculate confidence
        confidence = 'high' if abs(probability - 0.5) > 0.3 else 'medium' if abs(probability - 0.5) > 0.15 else 'low'

        # Assign grade
        if lead_score >= 90:
            grade = 'A+'
        elif lead_score >= 80:
            grade = 'A'
        elif lead_score >= 70:
            grade = 'B'
        elif lead_score >= 60:
            grade = 'C'
        elif lead_score >= 50:
            grade = 'D'
        else:
            grade = 'F'

        # Response
        response = {
            'lead_id': lead_id,
            'lead_score': lead_score,
            'conversion_probability': round(probability, 4),
            'confidence': confidence,
            'grade': grade,
            'predicted_at': datetime.now().isoformat(),
            'model_version': MODEL_VERSION
        }

        logger.info(f"Prediction for {lead_id}: score={lead_score}, prob={probability:.4f}")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e)
        }), 500


@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    """
    Batch prediction endpoint

    Request body:
    {
        "leads": [
            {"lead_id": "lead_1", "industry": "Tech", ...},
            {"lead_id": "lead_2", "industry": "Finance", ...}
        ]
    }

    Response:
    {
        "predictions": [
            {"lead_id": "lead_1", "lead_score": 85, ...},
            {"lead_id": "lead_2", "lead_score": 72, ...}
        ],
        "total": 2,
        "predicted_at": "2025-10-23T10:30:00"
    }
    """
    try:
        data = request.get_json()
        leads = data.get('leads', [])

        if not leads:
            return jsonify({'error': 'No leads provided'}), 400

        predictions = []

        for lead_data in leads:
            lead_id = lead_data.get('lead_id', 'unknown')

            try:
                # Preprocess
                X = preprocess_input(lead_data)

                # Predict
                probability = MODEL.predict_proba(X)[0, 1]
                lead_score = int(probability * 100)

                # Grade
                if lead_score >= 80:
                    grade = 'A'
                elif lead_score >= 70:
                    grade = 'B'
                elif lead_score >= 60:
                    grade = 'C'
                else:
                    grade = 'D'

                predictions.append({
                    'lead_id': lead_id,
                    'lead_score': lead_score,
                    'conversion_probability': round(probability, 4),
                    'grade': grade
                })

            except Exception as e:
                logger.error(f"Error predicting {lead_id}: {str(e)}")
                predictions.append({
                    'lead_id': lead_id,
                    'error': str(e)
                })

        response = {
            'predictions': predictions,
            'total': len(predictions),
            'predicted_at': datetime.now().isoformat(),
            'model_version': MODEL_VERSION
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Batch prediction failed',
            'message': str(e)
        }), 500


@app.route('/feature-importance', methods=['GET'])
def feature_importance():
    """
    Get feature importance from model

    Response:
    {
        "features": [
            {"feature": "email_opens_30d", "importance": 0.15},
            {"feature": "page_views_30d", "importance": 0.12},
            ...
        ]
    }
    """
    try:
        importance = MODEL.feature_importances_
        feature_importance_list = [
            {'feature': fname, 'importance': float(imp)}
            for fname, imp in zip(FEATURE_NAMES, importance)
        ]
        feature_importance_list.sort(key=lambda x: x['importance'], reverse=True)

        return jsonify({
            'features': feature_importance_list[:20],  # Top 20
            'model_version': MODEL_VERSION
        }), 200

    except Exception as e:
        logger.error(f"Feature importance error: {str(e)}")
        return jsonify({
            'error': 'Failed to get feature importance',
            'message': str(e)
        }), 500


# Initialize model on startup
@app.before_first_request
def initialize():
    """Initialize model before first request"""
    model_path = os.getenv('MODEL_PATH', 'models/lead_scoring_v1.json')
    load_model(model_path)


if __name__ == '__main__':
    # For local development
    load_model()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False)
