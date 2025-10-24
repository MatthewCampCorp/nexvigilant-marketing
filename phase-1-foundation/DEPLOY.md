# Phase 1: Data Foundation Deployment Guide

## What You're Building

A production-ready, three-layer data warehouse on BigQuery that powers the entire Autonomous Marketing Engine:

- **Bronze Layer (Raw)**: 7 data sources, 20+ tables, exact copies from source systems
- **Silver Layer (Staging)**: Cleaned, unified, 8 core analytical tables including Customer 360
- **Gold Layer (Marts)**: 8 business-ready analytical tables optimized for dashboards and ML

**Total**: 36 tables + views across 3 layers

---

## Prerequisites

### 1. Google Cloud Platform Setup

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project nexvigilant-marketing-prod

# Enable APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerydatatransfer.googleapis.com
gcloud services enable storage.googleapis.com
```

### 2. dbt Installation

```bash
# Install dbt-bigquery
pip install dbt-bigquery

# Verify installation
dbt --version
```

### 3. Fivetran/Data Integration Setup

Sign up for Fivetran or equivalent ETL tool to sync data from:
- Salesforce CRM
- Google Analytics 360
- Firebase
- Google Ads
- Braze
- Shopify
- Zendesk

---

## Deployment Steps

### Step 1: Create BigQuery Datasets

```bash
# Navigate to schemas directory
cd phase-1-foundation/bigquery-schemas

# Create Bronze layer (raw data)
bq mk --dataset \
  --location=US \
  --description="Raw data from source systems (Bronze layer)" \
  nexvigilant-marketing-prod:raw_data

# Create Silver layer (staging)
bq mk --dataset \
  --location=US \
  --description="Cleaned and unified data (Silver layer)" \
  nexvigilant-marketing-prod:staging

# Create Gold layer (marts)
bq mk --dataset \
  --location=US \
  --description="Business-ready analytical tables (Gold layer)" \
  nexvigilant-marketing-prod:marts

# Create test failures dataset
bq mk --dataset \
  --location=US \
  --description="dbt test failures" \
  nexvigilant-marketing-prod:test_failures
```

### Step 2: Create Bronze Layer Tables

```bash
# Execute Bronze layer schema
bq query --use_legacy_sql=false < 01_bronze_raw_schemas.sql

# Verify tables created
bq ls --max_results=100 nexvigilant-marketing-prod:raw_data
```

**Expected output**: 20 tables created
- salesforce_leads
- salesforce_accounts
- salesforce_opportunities
- ga360_sessions
- ga360_events
- firebase_events
- google_ads_campaigns
- google_ads_keywords
- braze_email_sends
- braze_email_events
- shopify_orders
- shopify_order_line_items
- zendesk_tickets
- data_quality_checks

### Step 3: Create Silver Layer Tables

```bash
# Execute Silver layer schema
bq query --use_legacy_sql=false < 02_silver_staging_schemas.sql

# Verify tables created
bq ls --max_results=100 nexvigilant-marketing-prod:staging
```

**Expected output**: 8 tables + 3 views
- customer_360 ✅ (CRITICAL - unified customer view)
- leads
- web_events
- email_engagement
- transactions
- ad_performance
- support_tickets
- products

### Step 4: Create Gold Layer Tables

```bash
# Execute Gold layer schema
bq query --use_legacy_sql=false < 03_gold_marts_schemas.sql

# Verify tables created
bq ls --max_results=100 nexvigilant-marketing-prod:marts
```

**Expected output**: 8 tables + 2 materialized views
- marketing_attribution
- customer_cohorts
- campaign_performance
- product_performance
- customer_health_scores
- lead_scores
- executive_kpis
- ml_features

### Step 5: Configure Fivetran Connectors

For each data source, configure Fivetran:

1. **Salesforce**:
   - Destination: `raw_data.salesforce_*`
   - Sync frequency: 24 hours
   - Tables: Accounts, Contacts, Leads, Opportunities

2. **Google Analytics 360**:
   - Destination: `raw_data.ga360_*`
   - Sync frequency: Daily export
   - Tables: Sessions, Events

3. **Firebase**:
   - Destination: `raw_data.firebase_events`
   - Sync frequency: Daily export
   - Intraday updates: Optional

4. **Google Ads**:
   - Destination: `raw_data.google_ads_*`
   - Sync frequency: 24 hours
   - Tables: Campaigns, Keywords

5. **Braze**:
   - Destination: `raw_data.braze_*`
   - Sync frequency: 6 hours
   - Tables: Email Sends, Email Events

6. **Shopify**:
   - Destination: `raw_data.shopify_*`
   - Sync frequency: 6 hours
   - Tables: Orders, Order Line Items, Customers

7. **Zendesk**:
   - Destination: `raw_data.zendesk_tickets`
   - Sync frequency: 6 hours

### Step 6: Configure dbt

```bash
# Navigate to dbt project
cd phase-1-foundation/dbt-project

# Create profiles.yml
mkdir -p ~/.dbt
cat > ~/.dbt/profiles.yml <<EOF
nexvigilant_marketing:
  target: prod
  outputs:
    prod:
      type: bigquery
      method: oauth
      project: nexvigilant-marketing-prod
      dataset: staging
      threads: 4
      timeout_seconds: 300
      location: US
      priority: interactive

    dev:
      type: bigquery
      method: oauth
      project: nexvigilant-marketing-prod
      dataset: dev_staging
      threads: 4
      timeout_seconds: 300
      location: US
      priority: interactive
EOF

# Test connection
dbt debug
```

**Expected output**: "All checks passed!"

### Step 7: Install dbt Dependencies

```bash
# Create packages.yml
cat > packages.yml <<EOF
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  - package: calogica/dbt_expectations
    version: 0.10.1
  - package: dbt-labs/codegen
    version: 0.12.1
EOF

# Install packages
dbt deps
```

### Step 8: Run dbt Models

```bash
# Full refresh (first time)
dbt run --full-refresh

# Run with tests
dbt build

# Generate documentation
dbt docs generate
dbt docs serve
```

**Expected output**:
```
Completed successfully

Done. PASS=15 WARN=0 ERROR=0 SKIP=0 TOTAL=15
```

---

## Verification & Testing

### 1. Data Quality Checks

```sql
-- Check customer_360 row count
SELECT COUNT(*) as total_customers
FROM `nexvigilant-marketing-prod.staging.customer_360`;
-- Expected: > 0

-- Check for duplicates
SELECT
  customer_id,
  COUNT(*) as duplicate_count
FROM `nexvigilant-marketing-prod.staging.customer_360`
GROUP BY customer_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows

-- Check profile completeness
SELECT
  CASE
    WHEN profile_completeness_score >= 80 THEN 'Complete'
    WHEN profile_completeness_score >= 50 THEN 'Partial'
    ELSE 'Incomplete'
  END AS completeness_category,
  COUNT(*) as customer_count,
  ROUND(AVG(profile_completeness_score), 2) as avg_score
FROM `nexvigilant-marketing-prod.staging.customer_360`
GROUP BY completeness_category;
```

### 2. Data Freshness

```sql
-- Check last update time
SELECT
  MAX(dbt_updated_at) as last_refresh,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(dbt_updated_at), HOUR) as hours_since_refresh
FROM `nexvigilant-marketing-prod.staging.customer_360`;
-- Expected: < 24 hours
```

### 3. Sample Queries

```sql
-- High-value customers
SELECT
  customer_id,
  full_name,
  company,
  total_revenue,
  lifetime_value,
  last_seen_date
FROM `nexvigilant-marketing-prod.staging.customer_360`
WHERE is_customer = TRUE
  AND total_revenue > 10000
ORDER BY total_revenue DESC
LIMIT 10;

-- Active leads needing follow-up
SELECT
  customer_id,
  email,
  full_name,
  lifecycle_stage,
  last_seen_date,
  engagement_score
FROM `nexvigilant-marketing-prod.staging.customer_360`
WHERE lifecycle_stage = 'mql'
  AND last_seen_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY engagement_score DESC;
```

---

## Scheduling & Automation

### Option 1: Cloud Scheduler + Cloud Functions

```bash
# Create Cloud Function to trigger dbt
gcloud functions deploy dbt-daily-run \
  --runtime python39 \
  --trigger-http \
  --entry-point run_dbt \
  --set-env-vars DBT_PROJECT_DIR=/dbt-project

# Schedule daily run at 6 AM
gcloud scheduler jobs create http dbt-daily-run \
  --schedule="0 6 * * *" \
  --uri="https://us-central1-nexvigilant-marketing-prod.cloudfunctions.net/dbt-daily-run" \
  --http-method=POST
```

### Option 2: dbt Cloud

1. Sign up: https://cloud.getdbt.com
2. Connect to BigQuery
3. Create job:
   - Run: `dbt build`
   - Schedule: Daily at 6 AM
   - On failure: Send Slack alert

---

## Monitoring & Alerts

### Set Up Alerts

```sql
-- Create alert for data freshness
CREATE OR REPLACE VIEW `nexvigilant-marketing-prod.staging.v_data_freshness_alerts` AS
SELECT
  'customer_360' as table_name,
  MAX(dbt_updated_at) as last_refresh,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(dbt_updated_at), HOUR) as hours_since_refresh,
  CASE
    WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(dbt_updated_at), HOUR) > 24
    THEN 'ALERT'
    ELSE 'OK'
  END as status
FROM `nexvigilant-marketing-prod.staging.customer_360`;
```

### Connect to Monitoring Tools

- **Datadog**: Install BigQuery integration
- **PagerDuty**: Set up alerts for dbt failures
- **Slack**: Webhook notifications on test failures

---

## Cost Optimization

### 1. Enable Table Partitioning

✅ Already implemented in schemas:
- All large tables partitioned by date
- Clustering on high-cardinality columns
- Partition expiration after 90 days (Bronze) / 1 year (Silver) / 2 years (Gold)

### 2. Monitor Costs

```bash
# Check BigQuery costs
bq ls --max_results=1000 --format=prettyjson \
  | jq '.[] | {table: .id, size_mb: (.numBytes/1048576)}'

# Total storage cost estimate
bq ls --max_results=1000 --format=json \
  | jq '[.[] | .numBytes] | add / 1099511627776 * 0.02'
```

**Expected monthly cost**: $200-500 for early stage

### 3. Optimize Queries

- Always use `WHERE` clauses on partition columns
- Use `LIMIT` for exploratory queries
- Cache repeated queries (automatic in BigQuery)
- Use clustering for common filter columns

---

## Troubleshooting

### Issue: dbt models failing

```bash
# Check logs
dbt run --debug

# Run single model
dbt run --select stg_customer_360

# Full refresh
dbt run --full-refresh --select stg_customer_360
```

### Issue: Fivetran sync failures

1. Check Fivetran dashboard for errors
2. Verify API credentials haven't expired
3. Check rate limits on source systems
4. Review BigQuery quotas

### Issue: Data quality test failures

```bash
# View test failures
SELECT * FROM `nexvigilant-marketing-prod.test_failures.customer_360_unique_key`
ORDER BY invocation_time DESC
LIMIT 100;

# Re-run tests
dbt test --select stg_customer_360
```

---

## Success Criteria

✅ **Bronze Layer**: All 20 tables created and receiving data
✅ **Silver Layer**: customer_360 has >0 rows with no duplicates
✅ **Gold Layer**: All 8 marts created successfully
✅ **dbt**: All models run without errors
✅ **Data Freshness**: < 24 hours for all tables
✅ **Data Quality**: >95% of tests passing
✅ **Cost**: < $500/month
✅ **Performance**: All queries < 5 seconds

---

## Next Steps: Phase 2 (Predictive AI)

Once data foundation is stable:

1. **Lead Scoring Model**:
   - Use `ml_features` mart
   - Train XGBoost model in Vertex AI
   - Deploy to Salesforce

2. **Content Generation**:
   - Use customer_360 for personalization
   - Integrate Gemini API
   - Generate email subject lines

3. **Churn Prediction**:
   - Use customer_health_scores mart
   - Train churn model
   - Alert Customer Success

---

**Deployment Time**: 2-3 days for initial setup
**Ongoing Maintenance**: 2-4 hours/week

**Ready to deploy?** Start with Step 1! 🚀
