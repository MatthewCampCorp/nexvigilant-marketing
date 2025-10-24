# Comprehensive Testing & Error Framework
## Autonomous Marketing Engine

## Overview

A production AI system requires rigorous testing across multiple dimensions. This framework establishes comprehensive testing, error handling, and quality assurance processes to ensure the Autonomous Marketing Engine operates reliably, accurately, and safely.

**Testing Philosophy**: "Test early, test often, test everything that matters"

---

## Testing Pyramid for AI/ML Systems

```
                    ┌─────────────────┐
                    │  Manual Testing │  ← 5%
                    │  User Acceptance│
                    └─────────────────┘
                  ┌───────────────────────┐
                  │   End-to-End Tests    │  ← 10%
                  │   Journey Validation  │
                  └───────────────────────┘
              ┌─────────────────────────────────┐
              │   Integration Tests             │  ← 20%
              │   API, Data Pipeline, Reverse ETL│
              └─────────────────────────────────┘
          ┌─────────────────────────────────────────┐
          │   ML Model Tests                        │  ← 30%
          │   Accuracy, Drift, Bias, Performance    │
          └─────────────────────────────────────────┘
      ┌───────────────────────────────────────────────────┐
      │   Data Quality Tests                              │  ← 35%
      │   Schema, Completeness, Freshness, Anomalies      │
      └───────────────────────────────────────────────────┘
```

---

## Part 1: Testing Strategy Overview

### Testing Categories

| Test Category | Coverage | Frequency | Automation Level |
|---------------|----------|-----------|------------------|
| **Data Quality** | Schema, nulls, duplicates, anomalies | Real-time + Daily | 100% automated |
| **ML Model Validation** | Accuracy, bias, drift, explainability | Pre-deployment + Weekly | 95% automated |
| **Integration Tests** | API endpoints, data flows, ETL/Reverse ETL | On deploy + Daily | 90% automated |
| **Performance Tests** | Latency, throughput, load | Weekly | 85% automated |
| **End-to-End Tests** | Complete customer journeys | Daily | 70% automated |
| **Chaos Engineering** | Resilience, failover, recovery | Monthly | 50% automated |
| **Security Tests** | PII handling, access control, encryption | Quarterly | 80% automated |
| **A/B Tests** | Campaign effectiveness, model performance | Continuous | 100% automated |

### Test Environments

```
┌─────────────────────────────────────────────────────────────┐
│                        ENVIRONMENTS                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  DEV                STAGING               PRODUCTION         │
│  ├─ Unit tests      ├─ Integration       ├─ Smoke tests     │
│  ├─ Local data      ├─ Staging data      ├─ Canary deploy  │
│  ├─ Fast feedback   ├─ Pre-prod testing  ├─ Shadow mode     │
│  └─ Rapid iteration └─ Full validation   └─ A/B testing     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Environment Specifications**:

**Dev Environment**:
- Purpose: Rapid development and debugging
- Data: Synthetic or anonymized sample data (1% of prod)
- Scale: Single node, minimal resources
- CI/CD: Automated tests on every commit

**Staging Environment**:
- Purpose: Pre-production validation
- Data: Anonymized production data (10% sample)
- Scale: 50% of production capacity
- CI/CD: Automated deployment from main branch

**Production Environment**:
- Purpose: Live customer-facing system
- Data: Real customer data (full dataset)
- Scale: Auto-scaling based on load
- Deployment: Blue-green with canary rollout

### Testing Gates (Quality Gates)

Code/models cannot progress to next environment without passing:

**Gate 1: Dev → Staging**
- ✅ All unit tests pass (100%)
- ✅ Code coverage >80%
- ✅ No critical security vulnerabilities
- ✅ Data quality tests pass on dev data
- ✅ ML model accuracy meets minimum threshold (if applicable)

**Gate 2: Staging → Production**
- ✅ All integration tests pass
- ✅ Performance tests meet SLA (latency, throughput)
- ✅ No data quality alerts in staging
- ✅ ML model validation complete (bias, drift checks)
- ✅ Manual approval from product owner
- ✅ Rollback plan documented

**Gate 3: Production Deployment**
- ✅ Canary deployment (5% traffic) successful for 24 hours
- ✅ No critical errors in monitoring
- ✅ Business metrics stable (conversion rate, ROAS)
- ✅ Gradual rollout: 5% → 25% → 50% → 100% over 3 days

---

## Part 2: Data Quality Testing Framework

### Critical Data Quality Dimensions

1. **Completeness**: Are all expected fields populated?
2. **Accuracy**: Do values make sense?
3. **Consistency**: Do related fields agree?
4. **Timeliness**: Is data fresh enough?
5. **Uniqueness**: Are there unexpected duplicates?
6. **Validity**: Do values conform to expected formats/ranges?

### Data Quality Test Suite

**Implemented with**: Great Expectations, dbt tests, custom BigQuery queries

**Test Levels**:

#### Level 1: Schema Validation (Immediate Failure)
```python
# great_expectations/expectations/raw_salesforce_leads.json
{
  "expectation_suite_name": "raw_salesforce_leads",
  "expectations": [
    {
      "expectation_type": "expect_table_columns_to_match_set",
      "kwargs": {
        "column_set": ["Id", "Email", "FirstName", "LastName", "Company", "CreatedDate", "LastModifiedDate"]
      },
      "meta": {
        "criticality": "critical",
        "action_on_failure": "stop_pipeline"
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_unique",
      "kwargs": {
        "column": "Id"
      }
    },
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": {
        "column": "Email"
      }
    },
    {
      "expectation_type": "expect_column_values_to_match_regex",
      "kwargs": {
        "column": "Email",
        "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      }
    }
  ]
}
```

#### Level 2: Completeness Checks (Warning)
```sql
-- dbt test: Check null rates for critical fields
-- File: tests/data_quality/check_null_rates.sql

WITH null_rates AS (
  SELECT
    'Email' AS field_name,
    COUNTIF(Email IS NULL) AS null_count,
    COUNT(*) AS total_count,
    SAFE_DIVIDE(COUNTIF(Email IS NULL), COUNT(*)) AS null_rate
  FROM {{ ref('raw_salesforce_leads') }}
  WHERE DATE(CreatedDate) >= CURRENT_DATE() - 1  -- Yesterday's data

  UNION ALL

  SELECT
    'Company' AS field_name,
    COUNTIF(Company IS NULL) AS null_count,
    COUNT(*) AS total_count,
    SAFE_DIVIDE(COUNTIF(Company IS NULL), COUNT(*)) AS null_rate
  FROM {{ ref('raw_salesforce_leads') }}
  WHERE DATE(CreatedDate) >= CURRENT_DATE() - 1
)

SELECT *
FROM null_rates
WHERE null_rate > 0.05  -- Fail if >5% null rate
```

#### Level 3: Freshness Checks (Critical for Real-Time)
```yaml
# dbt_project.yml
sources:
  - name: salesforce
    freshness:
      warn_after: {count: 6, period: hour}
      error_after: {count: 24, period: hour}
    tables:
      - name: leads
        loaded_at_field: _fivetran_synced
      - name: contacts
        loaded_at_field: _fivetran_synced
```

#### Level 4: Anomaly Detection (Statistical)
```sql
-- Detect volume anomalies using Z-score
WITH daily_volumes AS (
  SELECT
    DATE(event_timestamp) AS date,
    COUNT(*) AS event_count
  FROM `raw_ga360_events`
  WHERE DATE(event_timestamp) >= CURRENT_DATE() - 30
  GROUP BY date
),

volume_stats AS (
  SELECT
    AVG(event_count) AS mean_volume,
    STDDEV(event_count) AS stddev_volume
  FROM daily_volumes
),

today_volume AS (
  SELECT COUNT(*) AS todays_count
  FROM `raw_ga360_events`
  WHERE DATE(event_timestamp) = CURRENT_DATE()
)

SELECT
  todays_count,
  mean_volume,
  stddev_volume,
  (todays_count - mean_volume) / stddev_volume AS z_score,
  CASE
    WHEN ABS((todays_count - mean_volume) / stddev_volume) > 3 THEN 'CRITICAL_ANOMALY'
    WHEN ABS((todays_count - mean_volume) / stddev_volume) > 2 THEN 'WARNING'
    ELSE 'NORMAL'
  END AS status
FROM today_volume, volume_stats
WHERE ABS((todays_count - mean_volume) / stddev_volume) > 2  -- Alert if >2 standard deviations
```

#### Level 5: Cross-System Consistency
```sql
-- Check that all Salesforce leads appear in GA360 events
WITH salesforce_leads AS (
  SELECT DISTINCT email
  FROM `raw_salesforce_leads`
  WHERE DATE(CreatedDate) >= CURRENT_DATE() - 7
),

ga_users AS (
  SELECT DISTINCT user_id AS email
  FROM `raw_ga360_events`
  WHERE DATE(event_date) >= CURRENT_DATE() - 7
    AND user_id IS NOT NULL
),

missing_in_ga AS (
  SELECT sl.email
  FROM salesforce_leads sl
  LEFT JOIN ga_users ga ON sl.email = ga.email
  WHERE ga.email IS NULL
)

SELECT
  COUNT(*) AS missing_count,
  (SELECT COUNT(*) FROM salesforce_leads) AS total_leads,
  SAFE_DIVIDE(COUNT(*), (SELECT COUNT(*) FROM salesforce_leads)) AS missing_rate
FROM missing_in_ga
HAVING missing_rate > 0.10  -- Alert if >10% of leads missing from GA
```

### Automated Data Quality Dashboard

**BigQuery Scheduled Query** (runs daily at 6 AM):
```sql
-- Insert data quality metrics into monitoring table
CREATE OR REPLACE TABLE `monitoring.data_quality_daily` AS

WITH quality_metrics AS (
  -- Schema compliance
  SELECT
    CURRENT_DATE() AS report_date,
    'raw_salesforce_leads' AS table_name,
    'schema_compliance' AS test_type,
    CASE WHEN (
      SELECT COUNT(*)
      FROM `INFORMATION_SCHEMA.COLUMNS`
      WHERE table_name = 'raw_salesforce_leads'
    ) = 15 THEN 'PASS' ELSE 'FAIL' END AS status,
    NULL AS metric_value

  UNION ALL

  -- Freshness
  SELECT
    CURRENT_DATE() AS report_date,
    'raw_salesforce_leads' AS table_name,
    'freshness_hours' AS test_type,
    CASE WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(_fivetran_synced), HOUR) <= 6
         THEN 'PASS' ELSE 'FAIL' END AS status,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(_fivetran_synced), HOUR) AS metric_value
  FROM `raw_salesforce_leads`

  UNION ALL

  -- Null rate
  SELECT
    CURRENT_DATE() AS report_date,
    'raw_salesforce_leads' AS table_name,
    'email_null_rate' AS test_type,
    CASE WHEN SAFE_DIVIDE(COUNTIF(Email IS NULL), COUNT(*)) <= 0.05
         THEN 'PASS' ELSE 'FAIL' END AS status,
    SAFE_DIVIDE(COUNTIF(Email IS NULL), COUNT(*)) AS metric_value
  FROM `raw_salesforce_leads`
  WHERE DATE(CreatedDate) >= CURRENT_DATE() - 1

  -- Add more tests for each critical table...
)

SELECT * FROM quality_metrics;

-- Send alert if any critical tests fail
DECLARE failed_tests INT64;
SET failed_tests = (SELECT COUNT(*) FROM `monitoring.data_quality_daily` WHERE status = 'FAIL' AND report_date = CURRENT_DATE());

IF failed_tests > 0 THEN
  -- Trigger alert (Cloud Function webhook)
  SELECT ERROR(FORMAT('Data quality tests failed: %d critical failures', failed_tests));
END IF;
```

---

## Part 3: ML Model Testing Framework

### Pre-Deployment Validation Checklist

**Before ANY model goes to production**:

#### 1. Training Data Validation
```python
# scripts/testing/validate_training_data.py

import pandas as pd
from google.cloud import bigquery

def validate_training_data(dataset_table: str) -> dict:
    """
    Validate training dataset before model training

    Returns:
        dict: Validation results with pass/fail for each check
    """
    client = bigquery.Client()

    results = {}

    # Check 1: Sufficient data volume
    query = f"SELECT COUNT(*) as count FROM `{dataset_table}`"
    df = client.query(query).to_dataframe()
    min_required = 10000
    results['sufficient_volume'] = {
        'pass': df['count'][0] >= min_required,
        'actual': df['count'][0],
        'required': min_required
    }

    # Check 2: Class balance (for classification)
    query = f"""
    SELECT
      label,
      COUNT(*) as count,
      COUNT(*) / SUM(COUNT(*)) OVER() as percentage
    FROM `{dataset_table}`
    GROUP BY label
    """
    df = client.query(query).to_dataframe()

    # Fail if minority class is <5%
    min_class_pct = df['percentage'].min()
    results['class_balance'] = {
        'pass': min_class_pct >= 0.05,
        'min_class_percentage': min_class_pct,
        'distribution': df.to_dict('records')
    }

    # Check 3: No data leakage (future data in training set)
    query = f"""
    SELECT COUNT(*) as leakage_count
    FROM `{dataset_table}`
    WHERE created_date > label_date  -- Features created AFTER label
    """
    df = client.query(query).to_dataframe()
    results['no_data_leakage'] = {
        'pass': df['leakage_count'][0] == 0,
        'leakage_rows': df['leakage_count'][0]
    }

    # Check 4: Feature coverage (no excessive nulls)
    query = f"""
    SELECT
      column_name,
      COUNTIF(column_value IS NULL) / COUNT(*) as null_rate
    FROM `{dataset_table}`
    CROSS JOIN UNNEST(SPLIT(TO_JSON_STRING({dataset_table}))) as column_value
    GROUP BY column_name
    HAVING null_rate > 0.3  -- Flag features with >30% nulls
    """
    df = client.query(query).to_dataframe()
    results['feature_coverage'] = {
        'pass': len(df) == 0,
        'high_null_features': df.to_dict('records')
    }

    # Check 5: Temporal split (no time-based data leakage)
    query = f"""
    SELECT
      MIN(created_date) as train_min,
      MAX(created_date) as train_max,
      (SELECT MIN(created_date) FROM `{dataset_table.replace('train', 'test')}`) as test_min
    FROM `{dataset_table}`
    """
    df = client.query(query).to_dataframe()
    results['temporal_split'] = {
        'pass': df['train_max'][0] < df['test_min'][0],
        'train_end': str(df['train_max'][0]),
        'test_start': str(df['test_min'][0])
    }

    return results

# Usage
if __name__ == "__main__":
    validation = validate_training_data('nexvigilant-prod.ml_datasets.lead_scoring_train')

    all_passed = all([v['pass'] for v in validation.values()])

    if all_passed:
        print("✅ All training data validation checks passed!")
    else:
        print("❌ Training data validation FAILED:")
        for check, result in validation.items():
            if not result['pass']:
                print(f"  - {check}: {result}")
        exit(1)  # Fail CI/CD pipeline
```

#### 2. Model Performance Testing
```python
# scripts/testing/test_model_performance.py

import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)
from google.cloud import aiplatform, bigquery

def evaluate_model_performance(
    model_endpoint: str,
    test_dataset_table: str,
    model_type: str = 'classification'
) -> dict:
    """
    Comprehensive model performance evaluation
    """

    # Load test data
    client = bigquery.Client()
    query = f"SELECT * FROM `{test_dataset_table}`"
    test_df = client.query(query).to_dataframe()

    X_test = test_df.drop(['label', 'id'], axis=1)
    y_true = test_df['label']

    # Get predictions from Vertex AI endpoint
    endpoint = aiplatform.Endpoint(model_endpoint)
    predictions = endpoint.predict(instances=X_test.to_dict('records'))
    y_pred_proba = np.array([p['probability'] for p in predictions.predictions])
    y_pred = (y_pred_proba >= 0.5).astype(int)

    results = {}

    # Core metrics
    results['accuracy'] = accuracy_score(y_true, y_pred)
    results['precision'] = precision_score(y_true, y_pred)
    results['recall'] = recall_score(y_true, y_pred)
    results['f1_score'] = f1_score(y_true, y_pred)
    results['roc_auc'] = roc_auc_score(y_true, y_pred_proba)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    results['confusion_matrix'] = {
        'true_negatives': int(cm[0, 0]),
        'false_positives': int(cm[0, 1]),
        'false_negatives': int(cm[1, 0]),
        'true_positives': int(cm[1, 1])
    }

    # Threshold analysis
    thresholds = [0.3, 0.5, 0.7, 0.9]
    results['threshold_analysis'] = []
    for thresh in thresholds:
        y_pred_t = (y_pred_proba >= thresh).astype(int)
        results['threshold_analysis'].append({
            'threshold': thresh,
            'precision': precision_score(y_true, y_pred_t),
            'recall': recall_score(y_true, y_pred_t),
            'f1': f1_score(y_true, y_pred_t)
        })

    # Performance by segment (check for bias)
    if 'segment' in test_df.columns:
        results['performance_by_segment'] = []
        for segment in test_df['segment'].unique():
            mask = test_df['segment'] == segment
            results['performance_by_segment'].append({
                'segment': segment,
                'accuracy': accuracy_score(y_true[mask], y_pred[mask]),
                'precision': precision_score(y_true[mask], y_pred[mask]),
                'recall': recall_score(y_true[mask], y_pred[mask]),
                'sample_size': mask.sum()
            })

    # Validation gates
    results['validation'] = {
        'accuracy_pass': results['accuracy'] >= 0.80,
        'precision_pass': results['precision'] >= 0.75,
        'recall_pass': results['recall'] >= 0.70,
        'auc_pass': results['roc_auc'] >= 0.85,
        'all_passed': (
            results['accuracy'] >= 0.80 and
            results['precision'] >= 0.75 and
            results['recall'] >= 0.70 and
            results['roc_auc'] >= 0.85
        )
    }

    return results

# Usage
if __name__ == "__main__":
    results = evaluate_model_performance(
        model_endpoint='projects/123/locations/us-central1/endpoints/456',
        test_dataset_table='nexvigilant-prod.ml_datasets.lead_scoring_test'
    )

    print(f"Model Performance:")
    print(f"  Accuracy: {results['accuracy']:.3f}")
    print(f"  Precision: {results['precision']:.3f}")
    print(f"  Recall: {results['recall']:.3f}")
    print(f"  AUC-ROC: {results['roc_auc']:.3f}")

    if results['validation']['all_passed']:
        print("\n✅ Model passed all performance gates!")
    else:
        print("\n❌ Model FAILED performance validation:")
        for gate, passed in results['validation'].items():
            if not passed and gate != 'all_passed':
                print(f"  - {gate}")
        exit(1)
```

#### 3. Bias & Fairness Testing
```python
# scripts/testing/test_model_fairness.py

import pandas as pd
from google.cloud import bigquery

def test_fairness(
    predictions_table: str,
    protected_attributes: list = ['gender', 'age_group', 'geography']
) -> dict:
    """
    Test for algorithmic bias across protected characteristics

    Implements:
    - Demographic parity (equal positive prediction rate)
    - Equal opportunity (equal true positive rate)
    - Disparate impact (80% rule)
    """

    client = bigquery.Client()

    fairness_results = {}

    for attribute in protected_attributes:
        # Skip if attribute not available
        query = f"""
        SELECT COUNT(*) as count
        FROM `{predictions_table}`
        WHERE {attribute} IS NOT NULL
        """
        df = client.query(query).to_dataframe()
        if df['count'][0] == 0:
            continue

        # Calculate metrics by group
        query = f"""
        SELECT
          {attribute} as group_value,
          COUNT(*) as total,
          COUNTIF(predicted_label = 1) as positive_predictions,
          COUNTIF(actual_label = 1) as actual_positives,
          COUNTIF(predicted_label = 1 AND actual_label = 1) as true_positives,

          -- Rates
          SAFE_DIVIDE(COUNTIF(predicted_label = 1), COUNT(*)) as positive_prediction_rate,
          SAFE_DIVIDE(
            COUNTIF(predicted_label = 1 AND actual_label = 1),
            COUNTIF(actual_label = 1)
          ) as true_positive_rate
        FROM `{predictions_table}`
        WHERE {attribute} IS NOT NULL
        GROUP BY {attribute}
        """

        df = client.query(query).to_dataframe()

        # Demographic parity check
        max_ppr = df['positive_prediction_rate'].max()
        min_ppr = df['positive_prediction_rate'].min()
        demographic_parity_ratio = min_ppr / max_ppr if max_ppr > 0 else 0

        # Equal opportunity check
        max_tpr = df['true_positive_rate'].max()
        min_tpr = df['true_positive_rate'].min()
        equal_opportunity_ratio = min_tpr / max_tpr if max_tpr > 0 else 0

        # 80% rule (disparate impact)
        disparate_impact_pass = demographic_parity_ratio >= 0.80
        equal_opportunity_pass = equal_opportunity_ratio >= 0.80

        fairness_results[attribute] = {
            'group_metrics': df.to_dict('records'),
            'demographic_parity_ratio': demographic_parity_ratio,
            'equal_opportunity_ratio': equal_opportunity_ratio,
            'disparate_impact_pass': disparate_impact_pass,
            'equal_opportunity_pass': equal_opportunity_pass,
            'overall_pass': disparate_impact_pass and equal_opportunity_pass
        }

    return fairness_results

# Usage
if __name__ == "__main__":
    results = test_fairness(
        predictions_table='nexvigilant-prod.ml_predictions.lead_scoring_latest',
        protected_attributes=['geography', 'company_size']
    )

    all_passed = all([v['overall_pass'] for v in results.values()])

    if all_passed:
        print("✅ Model passed all fairness tests!")
    else:
        print("❌ Model FAILED fairness validation:")
        for attribute, metrics in results.items():
            if not metrics['overall_pass']:
                print(f"\n  Attribute: {attribute}")
                print(f"    Demographic parity ratio: {metrics['demographic_parity_ratio']:.3f}")
                print(f"    Equal opportunity ratio: {metrics['equal_opportunity_ratio']:.3f}")
                print(f"    Group breakdown:")
                for group in metrics['group_metrics']:
                    print(f"      {group['group_value']}: PPR={group['positive_prediction_rate']:.3f}, TPR={group['true_positive_rate']:.3f}")

        print("\n⚠️  Review model for potential bias. Consider:")
        print("  1. Removing or transforming biased features")
        print("  2. Rebalancing training data")
        print("  3. Applying fairness constraints during training")
        exit(1)
```

#### 4. Model Drift Detection
```python
# scripts/testing/detect_model_drift.py

import pandas as pd
from scipy import stats
from google.cloud import bigquery

def detect_drift(
    reference_data_table: str,  # Training data
    current_data_table: str,    # Recent production data
    features: list,
    drift_threshold: float = 0.05  # p-value threshold
) -> dict:
    """
    Detect data drift using statistical tests

    Methods:
    - Kolmogorov-Smirnov test for numerical features
    - Chi-square test for categorical features
    """

    client = bigquery.Client()

    # Load reference and current data
    ref_df = client.query(f"SELECT {','.join(features)} FROM `{reference_data_table}` LIMIT 10000").to_dataframe()
    cur_df = client.query(f"SELECT {','.join(features)} FROM `{current_data_table}` LIMIT 10000").to_dataframe()

    drift_results = {}

    for feature in features:
        # Skip if feature missing
        if feature not in ref_df.columns or feature not in cur_df.columns:
            continue

        # Determine if numerical or categorical
        if ref_df[feature].dtype in ['float64', 'int64']:
            # Kolmogorov-Smirnov test for numerical
            statistic, p_value = stats.ks_2samp(
                ref_df[feature].dropna(),
                cur_df[feature].dropna()
            )
            test_type = 'ks_test'
        else:
            # Chi-square test for categorical
            ref_counts = ref_df[feature].value_counts(normalize=True)
            cur_counts = cur_df[feature].value_counts(normalize=True)

            # Align indices
            all_categories = set(ref_counts.index).union(set(cur_counts.index))
            ref_freq = [ref_counts.get(cat, 0) for cat in all_categories]
            cur_freq = [cur_counts.get(cat, 0) for cat in all_categories]

            statistic, p_value = stats.chisquare(
                f_obs=[f * len(cur_df) for f in cur_freq],
                f_exp=[f * len(cur_df) for f in ref_freq]
            )
            test_type = 'chi_square'

        # Drift detected if p-value < threshold
        drift_detected = p_value < drift_threshold

        drift_results[feature] = {
            'test_type': test_type,
            'statistic': statistic,
            'p_value': p_value,
            'drift_detected': drift_detected,
            'severity': 'critical' if p_value < 0.01 else 'warning' if p_value < drift_threshold else 'none'
        }

    # Summary
    drift_summary = {
        'total_features': len(features),
        'features_with_drift': sum([v['drift_detected'] for v in drift_results.values()]),
        'critical_drift_features': [k for k, v in drift_results.items() if v['severity'] == 'critical'],
        'warning_drift_features': [k for k, v in drift_results.items() if v['severity'] == 'warning'],
        'drift_percentage': sum([v['drift_detected'] for v in drift_results.values()]) / len(features) * 100,
        'feature_details': drift_results
    }

    return drift_summary

# Usage
if __name__ == "__main__":
    drift = detect_drift(
        reference_data_table='nexvigilant-prod.ml_datasets.lead_scoring_train',
        current_data_table='nexvigilant-prod.staging.leads',
        features=['total_sessions', 'content_downloads', 'email_open_rate', 'company_size', 'industry']
    )

    print(f"Drift Detection Results:")
    print(f"  Features analyzed: {drift['total_features']}")
    print(f"  Features with drift: {drift['features_with_drift']} ({drift['drift_percentage']:.1f}%)")

    if drift['critical_drift_features']:
        print(f"\n❌ CRITICAL DRIFT detected in features:")
        for feature in drift['critical_drift_features']:
            details = drift['feature_details'][feature]
            print(f"    {feature}: p={details['p_value']:.4f}")
        print("\n⚠️  ACTION REQUIRED: Retrain model with recent data")
        exit(1)
    elif drift['warning_drift_features']:
        print(f"\n⚠️  WARNING: Moderate drift detected in features:")
        for feature in drift['warning_drift_features']:
            details = drift['feature_details'][feature]
            print(f"    {feature}: p={details['p_value']:.4f}")
        print("\n📊 Monitor closely. Consider retraining soon.")
    else:
        print("\n✅ No significant drift detected!")
```

---

## Part 4: Integration Testing

### API Endpoint Testing
```python
# tests/integration/test_prediction_api.py

import pytest
import requests
import time

BASE_URL = "https://api.nexvigilant.com/v1"
API_KEY = "test_api_key_staging"

class TestPredictionAPI:

    def test_lead_scoring_endpoint_success(self):
        """Test successful lead scoring prediction"""

        payload = {
            "lead_id": "test_lead_12345",
            "features": {
                "total_sessions": 5,
                "content_downloads": 2,
                "email_open_rate": 0.35,
                "company_size": "51-200",
                "industry": "Technology"
            }
        }

        response = requests.post(
            f"{BASE_URL}/predictions/lead-score",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert 'prediction' in data
        assert 'score' in data['prediction']
        assert 0 <= data['prediction']['score'] <= 100
        assert 'tier' in data['prediction']
        assert data['prediction']['tier'] in ['hot', 'warm', 'cool', 'cold']

    def test_lead_scoring_endpoint_invalid_input(self):
        """Test error handling for invalid input"""

        payload = {
            "lead_id": "test_lead_12345",
            "features": {
                "total_sessions": -5,  # Invalid: negative value
                "email_open_rate": 1.5  # Invalid: >1.0
            }
        }

        response = requests.post(
            f"{BASE_URL}/predictions/lead-score",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'validation' in data['error'].lower()

    def test_lead_scoring_endpoint_latency(self):
        """Test prediction latency meets SLA (<100ms)"""

        payload = {
            "lead_id": "test_lead_12345",
            "features": {
                "total_sessions": 5,
                "content_downloads": 2,
                "email_open_rate": 0.35,
                "company_size": "51-200",
                "industry": "Technology"
            }
        }

        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/predictions/lead-score",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        latency_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert latency_ms < 100, f"Latency {latency_ms:.2f}ms exceeds SLA of 100ms"

    def test_batch_prediction_endpoint(self):
        """Test batch prediction for multiple leads"""

        payload = {
            "leads": [
                {"lead_id": f"test_lead_{i}", "features": {...}}
                for i in range(100)
            ]
        }

        response = requests.post(
            f"{BASE_URL}/predictions/lead-score/batch",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert 'predictions' in data
        assert len(data['predictions']) == 100

# Run with: pytest tests/integration/test_prediction_api.py -v
```

### Data Pipeline Testing
```python
# tests/integration/test_data_pipelines.py

import pytest
from google.cloud import bigquery
import time

class TestDataPipelines:

    @pytest.fixture
    def bq_client(self):
        return bigquery.Client(project='nexvigilant-staging')

    def test_salesforce_to_bigquery_pipeline(self, bq_client):
        """Test Salesforce data appears in BigQuery within SLA"""

        # Insert test record in Salesforce (via API)
        test_lead_id = self.create_test_lead_in_salesforce()

        # Wait for Fivetran sync (up to 5 minutes for hourly sync)
        max_wait = 300  # 5 minutes
        start_time = time.time()
        found = False

        while (time.time() - start_time) < max_wait:
            query = f"""
            SELECT * FROM `nexvigilant-staging.raw_salesforce.leads`
            WHERE Id = '{test_lead_id}'
            """
            df = bq_client.query(query).to_dataframe()

            if len(df) > 0:
                found = True
                break

            time.sleep(30)  # Check every 30 seconds

        assert found, f"Test lead {test_lead_id} not found in BigQuery after {max_wait}s"

    def test_dbt_transformation_pipeline(self, bq_client):
        """Test dbt models create correct output"""

        # Run dbt model
        import subprocess
        result = subprocess.run(
            ["dbt", "run", "--models", "staging.customer_360", "--target", "staging"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"dbt run failed: {result.stderr}"

        # Validate output
        query = """
        SELECT
          COUNT(*) as row_count,
          COUNT(DISTINCT customer_id) as unique_customers,
          COUNTIF(email IS NULL) as null_emails
        FROM `nexvigilant-staging.staging.customer_360`
        """
        df = bq_client.query(query).to_dataframe()

        assert df['row_count'][0] > 0, "No rows in customer_360 table"
        assert df['null_emails'][0] == 0, "customer_360 has null emails"

    def test_reverse_etl_to_salesforce(self, bq_client):
        """Test Reverse ETL syncs scores back to Salesforce"""

        # Insert test score in BigQuery
        test_lead_id = "test_lead_reverse_etl_123"
        test_score = 85

        query = f"""
        INSERT INTO `nexvigilant-staging.marts.lead_scores`
        (lead_id, predicted_score, score_tier, scored_at)
        VALUES
        ('{test_lead_id}', {test_score}, 'hot', CURRENT_TIMESTAMP())
        """
        bq_client.query(query).result()

        # Trigger Hightouch sync (via API)
        self.trigger_hightouch_sync(sync_id='lead_scores_to_salesforce')

        # Wait for sync (up to 2 minutes)
        time.sleep(120)

        # Check Salesforce
        salesforce_score = self.get_salesforce_lead_score(test_lead_id)

        assert salesforce_score == test_score, \
            f"Score mismatch: BigQuery={test_score}, Salesforce={salesforce_score}"
```

---

## Part 5: Error Handling & Monitoring

### Centralized Error Handling

```python
# src/utils/error_handler.py

import logging
import traceback
from enum import Enum
from google.cloud import error_reporting
from google.cloud import monitoring_v3
import json

class ErrorSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MarketingEngineError(Exception):
    """Base exception for all marketing engine errors"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR, context: dict = None):
        self.message = message
        self.severity = severity
        self.context = context or {}
        super().__init__(self.message)

class DataQualityError(MarketingEngineError):
    """Raised when data quality checks fail"""
    pass

class ModelPerformanceError(MarketingEngineError):
    """Raised when model performance degrades below threshold"""
    pass

class IntegrationError(MarketingEngineError):
    """Raised when external API/service integration fails"""
    pass

class ErrorHandler:
    """Centralized error handling and reporting"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.error_client = error_reporting.Client()
        self.metrics_client = monitoring_v3.MetricServiceClient()
        self.logger = logging.getLogger(__name__)

    def handle_error(self, error: Exception, context: dict = None):
        """
        Handle errors with appropriate logging, alerting, and metrics
        """

        # Determine severity
        if isinstance(error, MarketingEngineError):
            severity = error.severity
            context = {**(context or {}), **error.context}
        else:
            severity = ErrorSeverity.ERROR
            context = context or {}

        # Log error
        log_message = f"{error.__class__.__name__}: {str(error)}"
        if context:
            log_message += f"\nContext: {json.dumps(context, indent=2)}"
        log_message += f"\n{traceback.format_exc()}"

        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Report to Cloud Error Reporting
        if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.error_client.report_exception()

        # Increment error metric
        self._increment_error_metric(
            error_type=error.__class__.__name__,
            severity=severity.value
        )

        # Send alerts for critical errors
        if severity == ErrorSeverity.CRITICAL:
            self._send_critical_alert(error, context)

    def _increment_error_metric(self, error_type: str, severity: str):
        """Increment error counter in Cloud Monitoring"""

        series = monitoring_v3.TimeSeries()
        series.metric.type = 'custom.googleapis.com/marketing_engine/errors'
        series.metric.labels['error_type'] = error_type
        series.metric.labels['severity'] = severity

        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )
        point = monitoring_v3.Point(
            {"interval": interval, "value": {"int64_value": 1}}
        )
        series.points = [point]

        project_name = f"projects/{self.project_id}"
        self.metrics_client.create_time_series(name=project_name, time_series=[series])

    def _send_critical_alert(self, error: Exception, context: dict):
        """Send alert to on-call team for critical errors"""

        # Send to PagerDuty
        self._send_pagerduty_alert(error, context)

        # Send to Slack
        self._send_slack_alert(error, context)

    def _send_slack_alert(self, error: Exception, context: dict):
        """Send alert to Slack channel"""

        import requests

        webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

        message = {
            "text": f"🚨 CRITICAL ERROR in Marketing Engine",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Critical Error Alert"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error Type:* `{error.__class__.__name__}`\n*Message:* {str(error)}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Context:*\n```{json.dumps(context, indent=2)}```"
                    }
                }
            ]
        }

        requests.post(webhook_url, json=message)

# Global error handler instance
error_handler = ErrorHandler(project_id='nexvigilant-prod')

# Usage decorator
def handle_errors(func):
    """Decorator to wrap functions with error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.handle_error(e, context={
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            })
            raise
    return wrapper

# Example usage
@handle_errors
def score_lead(lead_id: str):
    # ... scoring logic ...
    if data_quality_issue:
        raise DataQualityError(
            "Lead missing required fields",
            severity=ErrorSeverity.WARNING,
            context={'lead_id': lead_id, 'missing_fields': ['email', 'company']}
        )
```

---

**This is Part 1 of the comprehensive testing framework. Continue for:**
- Part 6: Performance & Load Testing
- Part 7: Chaos Engineering
- Part 8: Alerting & Incident Response
- Part 9: Testing Automation & CI/CD Integration

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Owner**: Data Engineering & QA Teams
**Next Review**: Quarterly
