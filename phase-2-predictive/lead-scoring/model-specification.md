# Lead Scoring Model Specification

## Model Overview

**Model Name**: Predictive Lead Scoring v1.0
**Model Type**: Binary Classification
**Business Objective**: Predict the probability that a lead will convert to a paying customer within 90 days
**Target Audience**: Sales and marketing teams
**Deployment Date**: Target Month 4 (Phase 2)

## Business Problem

### Current State
- Sales team receives 500+ new leads per week
- Only 10-15% of leads convert to opportunities
- Sales reps spend significant time on low-quality leads
- No systematic way to prioritize outreach
- Inconsistent lead qualification across team

### Desired State
- Every lead receives an AI-generated score (0-100) indicating conversion probability
- Sales team prioritizes high-scoring leads (80-100)
- Marketing nurtures mid-scoring leads (40-79) until they reach high score
- Low-scoring leads (<40) are deprioritized or disqualified
- 25% increase in lead-to-opportunity conversion rate
- 30% reduction in time from lead to first contact for high-value leads

### Success Metrics
- **Model Performance**: Accuracy >80%, AUC-ROC >0.85, Precision >75%
- **Business Impact**: Lead-to-opportunity conversion rate increases from 12% to 15%+
- **Operational**: 100% of leads scored within 24 hours of creation
- **Adoption**: 80%+ of sales team uses scores for prioritization within 30 days

## Model Specifications

### Target Variable

**Definition**: A lead is considered "converted" if they became a customer (Salesforce Opportunity with Stage = "Closed Won") within 90 days of lead creation.

**Label Creation Logic**:
```sql
SELECT
  lead_id,
  CASE
    WHEN converted_date IS NOT NULL
      AND DATE_DIFF(converted_date, created_date, DAY) <= 90
    THEN 1
    ELSE 0
  END AS label
FROM staging.leads
WHERE
  created_date >= '2024-01-01'  -- Historical data for training
  AND (
    converted_date IS NOT NULL  -- Converted leads
    OR DATE_DIFF(CURRENT_DATE(), created_date, DAY) > 90  -- Enough time has passed
  )
```

**Class Distribution** (expected):
- Positive (Converted): ~12% (6,000 leads)
- Negative (Not Converted): ~88% (44,000 leads)
- **Imbalance Handling**: Use SMOTE for oversampling or class weights in model

### Feature Engineering

#### Demographic Features (from Salesforce)

| Feature Name | Data Type | Description | Example Values |
|--------------|-----------|-------------|----------------|
| `title` | Categorical | Job title | "VP Sales", "Marketing Manager" |
| `seniority_level` | Categorical | Derived from title | "C-Level", "VP", "Director", "Manager", "Individual Contributor" |
| `job_function` | Categorical | Functional area | "Sales", "Marketing", "IT", "Finance", "Operations" |
| `industry` | Categorical | Company industry | "Technology", "Healthcare", "Finance" |
| `company_size` | Categorical | Number of employees | "1-10", "11-50", "51-200", "201-1000", "1000+" |
| `company_revenue` | Numerical | Annual revenue (if available) | 1000000 to 100000000 |
| `country` | Categorical | Lead's country | "United States", "Canada", "United Kingdom" |
| `state` | Categorical | Lead's state (US only) | "California", "New York", "Texas" |

**Feature Engineering**:
```sql
-- Seniority extraction from title
CASE
  WHEN LOWER(title) LIKE '%ceo%' OR LOWER(title) LIKE '%chief%' THEN 'C-Level'
  WHEN LOWER(title) LIKE '%vp%' OR LOWER(title) LIKE '%vice president%' THEN 'VP'
  WHEN LOWER(title) LIKE '%director%' THEN 'Director'
  WHEN LOWER(title) LIKE '%manager%' THEN 'Manager'
  ELSE 'Individual Contributor'
END AS seniority_level
```

#### Firmographic Features

| Feature Name | Data Type | Description | Example Values |
|--------------|-----------|-------------|----------------|
| `is_target_industry` | Boolean | Industry matches ICP | true/false |
| `is_target_size` | Boolean | Company size matches ICP (e.g., 50-500) | true/false |
| `domain_authority` | Numerical | Website domain authority (Moz/Ahrefs) | 0-100 |
| `employee_growth_rate` | Numerical | % growth in employees (LinkedIn) | -0.5 to 2.0 |
| `tech_stack_match` | Numerical | % of ICP technologies used | 0-100 |

#### Behavioral Features (from Website/GA360)

| Feature Name | Data Type | Description | Calculation |
|--------------|-----------|-------------|-------------|
| `total_sessions` | Numerical | Total website sessions | COUNT(DISTINCT session_id) |
| `total_pageviews` | Numerical | Total pages viewed | COUNT(page_view) |
| `avg_session_duration` | Numerical | Average time on site (seconds) | AVG(session_duration) |
| `visited_pricing_page` | Boolean | Visited pricing page | IF(page_path LIKE '%/pricing%', 1, 0) |
| `visited_demo_page` | Boolean | Visited demo page | IF(page_path LIKE '%/demo%', 1, 0) |
| `visited_case_studies` | Boolean | Visited case studies | IF(page_path LIKE '%/case-studies%', 1, 0) |
| `content_downloads` | Numerical | Number of whitepapers/ebooks downloaded | COUNT(download_event) |
| `video_views` | Numerical | Number of videos watched | COUNT(video_play) |
| `form_submissions` | Numerical | Number of forms submitted | COUNT(form_submit) |
| `search_queries` | Numerical | Number of site searches | COUNT(site_search) |
| `days_since_first_visit` | Numerical | Recency of first interaction | DATE_DIFF(CURRENT_DATE, first_visit_date, DAY) |
| `days_since_last_visit` | Numerical | Recency of last interaction | DATE_DIFF(CURRENT_DATE, last_visit_date, DAY) |
| `visit_frequency` | Numerical | Visits per week | total_sessions / weeks_active |

**Engagement Score** (composite):
```python
engagement_score = (
    visited_pricing_page * 10 +
    visited_demo_page * 15 +
    content_downloads * 5 +
    video_views * 3 +
    form_submissions * 8
)
```

#### Email Engagement Features (from Braze)

| Feature Name | Data Type | Description | Calculation |
|--------------|-----------|-------------|-------------|
| `emails_received` | Numerical | Total emails received | COUNT(email_send) |
| `emails_opened` | Numerical | Total emails opened | COUNT(email_open) |
| `emails_clicked` | Numerical | Total email clicks | COUNT(email_click) |
| `email_open_rate` | Numerical | % of emails opened | emails_opened / emails_received |
| `email_click_rate` | Numerical | % of emails clicked | emails_clicked / emails_opened |
| `last_email_engagement_days` | Numerical | Days since last open/click | DATE_DIFF(CURRENT_DATE, last_engagement_date, DAY) |

#### Source & Campaign Features

| Feature Name | Data Type | Description | Example Values |
|--------------|-----------|-------------|----------------|
| `lead_source` | Categorical | Original source | "Organic Search", "Paid Search", "Social", "Referral", "Direct" |
| `lead_medium` | Categorical | Medium | "cpc", "organic", "social", "email", "referral" |
| `lead_campaign` | Categorical | Campaign name | "Q1_Enterprise_Campaign" |
| `is_paid_source` | Boolean | Came from paid channel | true/false |
| `utm_content` | Categorical | Ad creative or link | "whitepaper_download" |

#### Social Signals (if available)

| Feature Name | Data Type | Description | Source |
|--------------|-----------|-------------|--------|
| `linkedin_connections` | Numerical | Number of connections | LinkedIn API |
| `linkedin_followers` | Numerical | Company followers | LinkedIn |
| `twitter_followers` | Numerical | Company followers | Twitter API |

#### Derived/Interaction Features

| Feature Name | Description | Calculation |
|--------------|-------------|-------------|
| `engagement_recency_ratio` | Balances engagement vs. recency | engagement_score / (days_since_last_visit + 1) |
| `seniority_size_score` | High seniority + large company | (seniority_level_encoded * company_size_encoded) |
| `intent_signal` | High-intent page visits | visited_pricing_page + visited_demo_page |

### Training Dataset

**Time Period**: January 2024 - September 2024 (9 months)
**Estimated Size**: 50,000 leads
**Positive Class**: ~6,000 (12%)
**Negative Class**: ~44,000 (88%)

**Train/Validation/Test Split**:
- Train: 70% (35,000 leads)
- Validation: 15% (7,500 leads) - for hyperparameter tuning
- Test: 15% (7,500 leads) - held out for final evaluation

**Temporal Split** (recommended):
- Train: Jan 2024 - July 2024
- Validation: Aug 2024
- Test: Sep 2024

This prevents data leakage and mirrors real-world deployment where we predict future leads.

### Feature Selection & Importance

**Methodology**:
1. **Univariate Analysis**: Calculate correlation with target, remove features with correlation < 0.05
2. **Multicollinearity**: Check VIF (Variance Inflation Factor), remove features with VIF > 10
3. **Recursive Feature Elimination**: Use model-based feature selection
4. **SHAP Values**: After training, use SHAP to understand feature importance

**Expected Top Features** (hypothesis):
1. `visited_pricing_page`
2. `content_downloads`
3. `seniority_level` (C-Level, VP)
4. `company_size` (target range)
5. `engagement_recency_ratio`
6. `email_click_rate`
7. `is_target_industry`

### Model Algorithm Selection

**Candidate Algorithms**:

1. **Logistic Regression** (Baseline)
   - Pros: Interpretable, fast, works well as baseline
   - Cons: Assumes linear relationships
   - Expected Performance: AUC ~0.75

2. **Random Forest**
   - Pros: Handles non-linear relationships, feature importance built-in
   - Cons: Less interpretable than logistic regression
   - Expected Performance: AUC ~0.80

3. **XGBoost** (Recommended)
   - Pros: State-of-the-art performance, handles imbalance well, feature importance
   - Cons: Requires hyperparameter tuning, less interpretable
   - Expected Performance: AUC ~0.85+

4. **Neural Network** (if data is sufficient)
   - Pros: Can capture complex patterns
   - Cons: Requires more data, less interpretable, longer training time
   - Expected Performance: AUC ~0.85

**Recommendation**: Start with XGBoost for best performance-interpretability balance.

### Hyperparameter Tuning

**XGBoost Hyperparameters to Tune**:

| Parameter | Search Space | Description |
|-----------|--------------|-------------|
| `max_depth` | [3, 5, 7, 10] | Maximum tree depth |
| `learning_rate` | [0.01, 0.05, 0.1] | Step size shrinkage |
| `n_estimators` | [100, 200, 500] | Number of boosting rounds |
| `min_child_weight` | [1, 3, 5] | Minimum sum of instance weight |
| `subsample` | [0.6, 0.8, 1.0] | Subsample ratio of training instances |
| `colsample_bytree` | [0.6, 0.8, 1.0] | Subsample ratio of features |
| `scale_pos_weight` | [1, 5, 10] | Balance of positive/negative weights (for imbalanced data) |

**Tuning Method**: Vertex AI Hyperparameter Tuning (Bayesian Optimization)
**Objective**: Maximize AUC-ROC
**Trials**: 50

### Model Evaluation

**Primary Metric**: **AUC-ROC** (Area Under Receiver Operating Characteristic Curve)
- Measures ability to distinguish between classes
- Threshold-agnostic
- Target: >0.85

**Secondary Metrics**:

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Accuracy** | >80% | Overall correctness |
| **Precision** | >75% | Of leads predicted as high-value, 75% actually convert (minimize false positives) |
| **Recall** | >70% | Capture 70% of all converting leads (minimize false negatives) |
| **F1-Score** | >0.70 | Harmonic mean of precision and recall |
| **Calibration** | Brier Score <0.15 | Predicted probabilities match actual conversion rates |

**Confusion Matrix Analysis** (expected on test set):

|  | Predicted Negative | Predicted Positive |
|--|--------------------|--------------------|
| **Actual Negative** | 6,000 (TN) | 600 (FP) |
| **Actual Positive** | 270 (FN) | 630 (TP) |

- **Precision** = 630 / (630 + 600) = 51% (needs improvement)
- **Recall** = 630 / (630 + 270) = 70%

**Score Distribution**:
- Aim for good separation between converted and non-converted leads
- Visualize with overlapping histograms

### Model Interpretability

**SHAP (SHapley Additive exPlanations)**:
- Calculate SHAP values for each prediction
- Create global feature importance plot
- Create individual explanation for sample leads

**Example SHAP Explanation**:
```
Lead Score: 87/100

Top Contributing Factors:
+ Visited pricing page 3 times: +15 points
+ Downloaded 2 whitepapers: +10 points
+ VP-level seniority: +8 points
+ Target industry (SaaS): +7 points
+ High email engagement: +5 points
- Last visit 14 days ago: -3 points
- Small company size (10 employees): -2 points
```

### Threshold Selection

**Score Tiers**:

| Tier | Score Range | Probability | Sales Action | Expected Conversion Rate |
|------|-------------|-------------|--------------|--------------------------|
| **Hot** | 80-100 | >60% | Immediate call within 24 hours | 60-80% |
| **Warm** | 50-79 | 30-60% | Email outreach, schedule call within 3 days | 30-60% |
| **Cool** | 30-49 | 15-30% | Nurture campaign, revisit in 2 weeks | 15-30% |
| **Cold** | 0-29 | <15% | Low-touch nurture or disqualify | <15% |

**Threshold Optimization**:
- Use Precision-Recall curve to select optimal threshold
- Business constraint: Minimize false positives (wasted sales time)
- Choose threshold where Precision = 75% (at least)

## Model Training Pipeline (Vertex AI)

### Training Pipeline Steps

**Step 1: Data Extraction**
```sql
-- Extract training data from BigQuery
CREATE OR REPLACE TABLE `nexvigilant-prod.ml_datasets.lead_scoring_train` AS
SELECT
  l.lead_id,
  -- Demographic features
  l.title,
  l.industry,
  l.company_size,
  l.country,
  -- Behavioral features
  b.total_sessions,
  b.visited_pricing_page,
  b.content_downloads,
  -- Email features
  e.email_open_rate,
  e.email_click_rate,
  -- Target variable
  l.converted_within_90_days AS label
FROM `staging.leads` l
LEFT JOIN `staging.lead_behavioral_features` b ON l.lead_id = b.lead_id
LEFT JOIN `staging.lead_email_features` e ON l.lead_id = e.lead_id
WHERE l.created_date BETWEEN '2024-01-01' AND '2024-09-30'
```

**Step 2: Feature Engineering** (Python/dbt)
```python
# feature_engineering.py
import pandas as pd

def engineer_features(df):
    # Seniority extraction
    df['seniority_level'] = df['title'].apply(extract_seniority)

    # Engagement score
    df['engagement_score'] = (
        df['visited_pricing_page'] * 10 +
        df['content_downloads'] * 5
    )

    # Recency features
    df['days_since_last_visit'] = (pd.Timestamp.now() - df['last_visit_date']).dt.days

    # One-hot encoding for categoricals
    df = pd.get_dummies(df, columns=['industry', 'seniority_level'])

    return df
```

**Step 3: Train Model**
```python
# train_model.py
import xgboost as xgb
from sklearn.model_selection import train_test_split
from google.cloud import bigquery, aiplatform

# Load data from BigQuery
client = bigquery.Client()
query = "SELECT * FROM `nexvigilant-prod.ml_datasets.lead_scoring_train`"
df = client.query(query).to_dataframe()

# Feature engineering
df = engineer_features(df)

# Split
X = df.drop(['lead_id', 'label'], axis=1)
y = df['label']
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, stratify=y)

# Handle imbalance
scale_pos_weight = len(y_train[y_train==0]) / len(y_train[y_train==1])

# Train XGBoost
model = xgb.XGBClassifier(
    max_depth=5,
    learning_rate=0.1,
    n_estimators=200,
    scale_pos_weight=scale_pos_weight,
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import roc_auc_score, precision_score, recall_score
y_pred_proba = model.predict_proba(X_val)[:, 1]
print(f"AUC-ROC: {roc_auc_score(y_val, y_pred_proba):.3f}")

# Upload to Vertex AI
aiplatform.init(project='nexvigilant-prod', location='us-central1')
model_vertex = aiplatform.Model.upload(
    display_name='lead-scoring-v1',
    artifact_uri='gs://nexvigilant-models/lead-scoring-v1',
    serving_container_image_uri='us-docker.pkg.dev/vertex-ai/prediction/xgboost-cpu.1-7:latest'
)
```

**Step 4: Deploy Model**
```python
# Deploy to endpoint for real-time predictions
endpoint = model_vertex.deploy(
    deployed_model_display_name='lead-scoring-v1-prod',
    machine_type='n1-standard-2',
    min_replica_count=1,
    max_replica_count=5,
    traffic_split={"0": 100}
)
```

### Batch Prediction Pipeline (Daily Scoring)

```python
# batch_predict.py
from google.cloud import aiplatform, bigquery

# Get new leads from yesterday
query = """
SELECT *
FROM staging.leads
WHERE created_date = CURRENT_DATE() - 1
  AND lead_score IS NULL
"""

# Batch prediction
batch_prediction_job = aiplatform.BatchPredictionJob.create(
    job_display_name='lead-scoring-daily',
    model_name='projects/nexvigilant-prod/locations/us-central1/models/lead-scoring-v1',
    bigquery_source='nexvigilant-prod.staging.leads_to_score',
    bigquery_destination_prefix='nexvigilant-prod',
    instances_format='bigquery',
    predictions_format='bigquery',
    machine_type='n1-standard-4'
)

batch_prediction_job.wait()

# Write scores back to BigQuery
client = bigquery.Client()
query = """
UPDATE staging.leads AS l
SET
  l.lead_score = p.predicted_probability * 100,
  l.score_tier = CASE
    WHEN p.predicted_probability >= 0.8 THEN 'Hot'
    WHEN p.predicted_probability >= 0.5 THEN 'Warm'
    WHEN p.predicted_probability >= 0.3 THEN 'Cool'
    ELSE 'Cold'
  END,
  l.last_scored_at = CURRENT_TIMESTAMP()
FROM predictions p
WHERE l.lead_id = p.lead_id
"""
client.query(query).result()
```

## Model Deployment & Integration

### Deployment Architecture

```
┌─────────────────┐
│   BigQuery      │
│  (New Leads)    │
└────────┬────────┘
         │
         │ Daily Batch Job (Cloud Scheduler)
         ▼
┌─────────────────┐
│  Vertex AI      │
│ Batch Prediction│
└────────┬────────┘
         │
         │ Predictions
         ▼
┌─────────────────┐
│   BigQuery      │
│ (Lead Scores)   │
└────────┬────────┘
         │
         │ Reverse ETL (Hightouch)
         ▼
┌─────────────────┐
│   Salesforce    │
│ (Lead Records)  │
└─────────────────┘
```

### Salesforce Integration

**Custom Fields to Add**:
- `AI_Lead_Score__c` (Number, 0-100)
- `Lead_Tier__c` (Picklist: Hot, Warm, Cool, Cold)
- `Last_Scored_Date__c` (DateTime)
- `Top_Engagement_Signals__c` (Text, comma-separated factors)

**Salesforce Flow** (Automation):
```
Trigger: AI_Lead_Score__c changes
Conditions:
  - If Lead_Tier__c = 'Hot' → Create Task for Lead Owner ("High-Priority Lead - Call within 24 hours")
  - If Lead_Tier__c = 'Warm' → Send Email Alert to Lead Owner
```

### Monitoring & Retraining

**Model Monitoring Metrics** (track weekly):
- **Prediction Distribution**: Ensure not drifting (e.g., all leads suddenly scored high)
- **Feature Distribution**: Alert if input data distribution changes significantly
- **Conversion Rate by Tier**: Actual conversion rates should match predicted probabilities
  - Hot tier should convert at 60-80%
  - Warm tier should convert at 30-60%
- **Model Performance Degradation**: Track AUC on recent data (use last 30 days as validation)

**Retraining Triggers**:
- **Scheduled**: Retrain every 3 months with latest data
- **Performance Degradation**: If AUC drops below 0.80 on recent data
- **Data Drift**: If feature distributions change significantly (KL divergence > threshold)
- **Business Change**: New lead sources, product changes, ICP shifts

**Model Versioning**:
- Use semantic versioning (v1.0, v1.1, v2.0)
- A/B test new model version vs. current production (20% traffic to new model)
- Promote to 100% if new model performs better

## Governance & Ethics

### Bias Mitigation

**Protected Characteristics** (never use as features):
- Gender
- Race/Ethnicity
- Age (individual)
- Religion

**Proxy Features** (use with caution, audit for bias):
- Geographic location (may correlate with demographics)
- Name (may indicate ethnicity)
- Company name (may indicate industry biases)

**Fairness Audits**:
- Quarterly review of model predictions by geography
- Ensure no systematic discrimination
- If bias detected, retrain with fairness constraints

### Transparency

**Model Card** (publish internally):
- Model purpose and use cases
- Training data details
- Performance metrics
- Known limitations
- Bias testing results
- Update frequency

**Explainability for Sales**:
- Provide SHAP-based explanations in Salesforce
- "Why did this lead get a score of 87?" → Show top contributing factors

## Timeline & Milestones

| Week | Milestone |
|------|-----------|
| Week 1-2 | Data preparation and feature engineering |
| Week 3 | Model training and hyperparameter tuning |
| Week 4 | Model evaluation and selection |
| Week 5 | Deployment to Vertex AI, Salesforce integration |
| Week 6 | Sales team training and pilot with 20% of leads |
| Week 7-8 | Monitor pilot, gather feedback, optimize |
| Week 9 | Full rollout to 100% of leads |
| Week 10+ | Ongoing monitoring and monthly performance reviews |

---

**Document Version**: 1.0
**Owner**: Data Science Team
**Reviewers**: Marketing, Sales, Legal
**Approval Date**: [Pending]
**Next Review**: Post-Deployment (Week 10)
