"""
Lead Scoring Model - Training Pipeline
NexVigilant Autonomous Marketing Engine

Trains XGBoost model to predict lead conversion probability (0-100 score)
Uses features from BigQuery marts.ml_features table
Deploys to Vertex AI for real-time predictions

Author: Data Science Team
Last Updated: 2025-10-23
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)
from google.cloud import bigquery, aiplatform, storage
import matplotlib.pyplot as plt
import seaborn as sns
import shap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LeadScoringModel:
    """
    Lead Scoring Model using XGBoost

    Features:
    - Demographic (10 features)
    - Behavioral (20 features)
    - Engagement (10 features)
    - Financial (10 features)

    Target: Binary classification (converted vs not converted)
    Output: Probability score 0-100
    """

    def __init__(self, project_id: str, dataset: str = "marts", model_version: str = "v1"):
        self.project_id = project_id
        self.dataset = dataset
        self.model_version = model_version
        self.model = None
        self.feature_names = None
        self.bq_client = bigquery.Client(project=project_id)

        # Feature groups
        self.demographic_features = [
            'industry', 'company_size_bucket', 'title_level',
            'country', 'account_age_days'
        ]

        self.behavioral_features = [
            'page_views_7d', 'page_views_30d', 'unique_pages_7d',
            'visits_7d', 'visits_30d', 'avg_session_duration_7d',
            'email_opens_7d', 'email_opens_30d', 'email_clicks_7d',
            'email_clicks_30d', 'content_downloads_30d',
            'days_since_last_visit', 'days_since_last_email_open'
        ]

        self.engagement_features = [
            'engagement_score', 'recency_score', 'frequency_score',
            'monetary_score', 'rfm_segment'
        ]

        self.financial_features = [
            'total_revenue', 'revenue_30d', 'revenue_90d',
            'average_order_value', 'total_orders', 'orders_30d',
            'days_since_last_purchase', 'lifetime_value'
        ]

        logger.info(f"Initialized LeadScoringModel v{model_version}")

    def extract_training_data(
        self,
        lookback_days: int = 90,
        min_training_samples: int = 1000
    ) -> pd.DataFrame:
        """
        Extract training data from BigQuery

        Args:
            lookback_days: How far back to look for training data
            min_training_samples: Minimum number of samples required

        Returns:
            DataFrame with features and labels
        """
        logger.info(f"Extracting training data (lookback: {lookback_days} days)")

        query = f"""
        WITH lead_features AS (
          SELECT
            -- Demographics
            COALESCE(industry, 'Unknown') as industry,
            COALESCE(company_size_bucket, 'Unknown') as company_size_bucket,
            COALESCE(title_level, 'Unknown') as title_level,
            COALESCE(country, 'Unknown') as country,
            COALESCE(account_age_days, 0) as account_age_days,

            -- Behavioral (30-day window)
            COALESCE(page_views_7d, 0) as page_views_7d,
            COALESCE(page_views_30d, 0) as page_views_30d,
            COALESCE(unique_pages_7d, 0) as unique_pages_7d,
            COALESCE(visits_7d, 0) as visits_7d,
            COALESCE(visits_30d, 0) as visits_30d,
            COALESCE(avg_session_duration_7d, 0) as avg_session_duration_7d,
            COALESCE(email_opens_7d, 0) as email_opens_7d,
            COALESCE(email_opens_30d, 0) as email_opens_30d,
            COALESCE(email_clicks_7d, 0) as email_clicks_7d,
            COALESCE(email_clicks_30d, 0) as email_clicks_30d,
            COALESCE(content_downloads_30d, 0) as content_downloads_30d,
            COALESCE(days_since_last_visit, 999) as days_since_last_visit,
            COALESCE(days_since_last_email_open, 999) as days_since_last_email_open,

            -- Engagement
            COALESCE(engagement_score, 0) as engagement_score,
            COALESCE(recency_score, 0) as recency_score,
            COALESCE(frequency_score, 0) as frequency_score,
            COALESCE(monetary_score, 0) as monetary_score,
            COALESCE(rfm_segment, 'Unknown') as rfm_segment,

            -- Financial
            COALESCE(total_revenue, 0) as total_revenue,
            COALESCE(revenue_30d, 0) as revenue_30d,
            COALESCE(revenue_90d, 0) as revenue_90d,
            COALESCE(average_order_value, 0) as average_order_value,
            COALESCE(total_orders, 0) as total_orders,
            COALESCE(orders_30d, 0) as orders_30d,
            COALESCE(days_since_last_purchase, 999) as days_since_last_purchase,
            COALESCE(lifetime_value, 0) as lifetime_value,

            -- Target variable
            label_converted as converted,

            -- Metadata for analysis
            entity_id as lead_id,
            snapshot_date

          FROM `{self.project_id}.{self.dataset}.ml_features`
          WHERE entity_type = 'lead'
            AND snapshot_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {lookback_days} DAY)
            AND label_converted IS NOT NULL  -- Must have ground truth
        )

        SELECT *
        FROM lead_features
        WHERE TRUE
          -- Exclude outliers
          AND page_views_30d < 10000  -- Likely bots
          AND email_opens_30d < 1000  -- Likely invalid
        """

        # Execute query
        df = self.bq_client.query(query).to_dataframe()

        logger.info(f"Extracted {len(df):,} training samples")

        # Validate minimum samples
        if len(df) < min_training_samples:
            raise ValueError(
                f"Insufficient training data: {len(df)} < {min_training_samples}"
            )

        # Check class balance
        conversion_rate = df['converted'].mean()
        logger.info(f"Conversion rate: {conversion_rate:.2%}")

        if conversion_rate < 0.01 or conversion_rate > 0.99:
            logger.warning(f"Imbalanced dataset: {conversion_rate:.2%} conversion rate")

        return df

    def preprocess_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Preprocess features for model training

        Args:
            df: Raw dataframe from BigQuery

        Returns:
            Tuple of (X features, y target)
        """
        logger.info("Preprocessing features")

        # Separate features and target
        feature_cols = (
            self.demographic_features +
            self.behavioral_features +
            self.engagement_features +
            self.financial_features
        )

        X = df[feature_cols].copy()
        y = df['converted'].astype(int)

        # One-hot encode categorical variables
        categorical_cols = ['industry', 'company_size_bucket', 'title_level', 'country', 'rfm_segment']
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)

        # Store feature names for later
        self.feature_names = X.columns.tolist()

        logger.info(f"Feature shape: {X.shape}")
        logger.info(f"Target shape: {y.shape}")
        logger.info(f"Features: {len(self.feature_names)}")

        return X, y

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        hyperparameters: Optional[Dict] = None
    ) -> Dict:
        """
        Train XGBoost model

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            hyperparameters: Model hyperparameters (optional)

        Returns:
            Training metrics
        """
        logger.info("Training XGBoost model")

        # Default hyperparameters
        if hyperparameters is None:
            hyperparameters = {
                'objective': 'binary:logistic',
                'eval_metric': 'auc',
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 1,
                'gamma': 0,
                'reg_alpha': 0,
                'reg_lambda': 1,
                'scale_pos_weight': 1,  # For imbalanced datasets
                'random_state': 42
            }

        # Handle class imbalance
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
        hyperparameters['scale_pos_weight'] = scale_pos_weight
        logger.info(f"Scale pos weight (class balance): {scale_pos_weight:.2f}")

        # Train model
        self.model = xgb.XGBClassifier(**hyperparameters)

        eval_set = [(X_train, y_train), (X_val, y_val)]

        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            eval_metric='auc',
            early_stopping_rounds=10,
            verbose=True
        )

        # Calculate metrics
        y_pred_train = self.model.predict(X_train)
        y_pred_val = self.model.predict(X_val)
        y_pred_proba_train = self.model.predict_proba(X_train)[:, 1]
        y_pred_proba_val = self.model.predict_proba(X_val)[:, 1]

        metrics = {
            'train_accuracy': accuracy_score(y_train, y_pred_train),
            'train_precision': precision_score(y_train, y_pred_train),
            'train_recall': recall_score(y_train, y_pred_train),
            'train_f1': f1_score(y_train, y_pred_train),
            'train_auc': roc_auc_score(y_train, y_pred_proba_train),
            'val_accuracy': accuracy_score(y_val, y_pred_val),
            'val_precision': precision_score(y_val, y_pred_val),
            'val_recall': recall_score(y_val, y_pred_val),
            'val_f1': f1_score(y_val, y_pred_val),
            'val_auc': roc_auc_score(y_val, y_pred_proba_val),
        }

        logger.info("Training Metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")

        return metrics

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Evaluate model on test set

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Test metrics
        """
        logger.info("Evaluating model on test set")

        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]

        metrics = {
            'test_accuracy': accuracy_score(y_test, y_pred),
            'test_precision': precision_score(y_test, y_pred),
            'test_recall': recall_score(y_test, y_pred),
            'test_f1': f1_score(y_test, y_pred),
            'test_auc': roc_auc_score(y_test, y_pred_proba),
        }

        logger.info("Test Metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")

        # Classification report
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"\nConfusion Matrix:\n{cm}")

        return metrics

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance from trained model

        Args:
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importance
        """
        importance = self.model.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        logger.info(f"\nTop {top_n} Features:")
        logger.info(feature_importance.head(top_n).to_string())

        return feature_importance

    def explain_predictions(self, X_sample: pd.DataFrame, num_samples: int = 100):
        """
        Generate SHAP explanations for model predictions

        Args:
            X_sample: Sample data for explanations
            num_samples: Number of samples to explain
        """
        logger.info("Generating SHAP explanations")

        # Create SHAP explainer
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X_sample.head(num_samples))

        # Summary plot
        shap.summary_plot(
            shap_values,
            X_sample.head(num_samples),
            show=False
        )
        plt.savefig('shap_summary.png', dpi=300, bbox_inches='tight')
        logger.info("SHAP summary plot saved to shap_summary.png")

        return shap_values

    def save_model(self, output_path: str):
        """
        Save trained model to disk

        Args:
            output_path: Path to save model
        """
        logger.info(f"Saving model to {output_path}")

        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save XGBoost model
        self.model.save_model(output_path)

        # Save feature names
        feature_names_path = output_path.replace('.json', '_features.json')
        with open(feature_names_path, 'w') as f:
            json.dump({
                'feature_names': self.feature_names,
                'model_version': self.model_version,
                'trained_at': datetime.now().isoformat()
            }, f, indent=2)

        logger.info(f"Model saved successfully")

    def predict_lead_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict lead scores (0-100)

        Args:
            X: Features dataframe

        Returns:
            Array of lead scores (0-100)
        """
        probabilities = self.model.predict_proba(X)[:, 1]
        scores = (probabilities * 100).round(0).astype(int)
        return scores


def main():
    """Main training pipeline"""
    parser = argparse.ArgumentParser(description='Train Lead Scoring Model')
    parser.add_argument('--project-id', required=True, help='GCP Project ID')
    parser.add_argument('--dataset', default='marts', help='BigQuery dataset')
    parser.add_argument('--lookback-days', type=int, default=90, help='Training data lookback period')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    parser.add_argument('--output-path', default='models/lead_scoring_v1.json', help='Model output path')

    args = parser.parse_args()

    # Initialize model
    model = LeadScoringModel(
        project_id=args.project_id,
        dataset=args.dataset
    )

    # Extract training data
    df = model.extract_training_data(lookback_days=args.lookback_days)

    # Preprocess
    X, y = model.preprocess_features(df)

    # Split data: 60% train, 20% val, 20% test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.4, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    logger.info(f"Train set: {len(X_train):,} samples")
    logger.info(f"Val set: {len(X_val):,} samples")
    logger.info(f"Test set: {len(X_test):,} samples")

    # Train model
    train_metrics = model.train(X_train, y_train, X_val, y_val)

    # Evaluate
    test_metrics = model.evaluate(X_test, y_test)

    # Feature importance
    feature_importance = model.get_feature_importance(top_n=20)

    # SHAP explanations
    model.explain_predictions(X_test)

    # Check if model meets minimum quality threshold
    if test_metrics['test_auc'] < 0.70:
        logger.warning(f"Model AUC ({test_metrics['test_auc']:.4f}) below threshold (0.70)")
        logger.warning("Consider collecting more data or feature engineering")

    # Save model
    model.save_model(args.output_path)

    logger.info("=" * 80)
    logger.info("Training Complete!")
    logger.info(f"Model saved to: {args.output_path}")
    logger.info(f"Test AUC: {test_metrics['test_auc']:.4f}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
