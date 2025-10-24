-- ============================================================
-- SILVER LAYER: Staging/Cleaned Data Schemas
-- ============================================================
-- Purpose: Cleaned, standardized, deduplicated data with basic transformations
-- Strategy: Type casting, null handling, deduplication, standardization
-- Data Quality: Enforce data quality rules, handle edge cases
-- Retention: 1 year
-- ============================================================

-- Project: nexvigilant-marketing-prod
-- Dataset: staging (Silver layer)

-- ============================================================
-- 1. STAGING: CUSTOMER 360 (Unified Customer View)
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.customer_360` (
  -- Primary identifier (generated)
  customer_id STRING NOT NULL,

  -- Identifiers from source systems
  salesforce_account_id STRING,
  salesforce_contact_id STRING,
  shopify_customer_id INT64,
  ga360_client_id STRING,
  firebase_user_id STRING,
  braze_external_user_id STRING,

  -- Demographics
  email STRING,
  first_name STRING,
  last_name STRING,
  full_name STRING,
  phone STRING,
  company STRING,
  title STRING,
  industry STRING,

  -- Geographic
  country STRING,
  state STRING,
  city STRING,
  postal_code STRING,

  -- Firmographics (B2B)
  company_size INT64,
  annual_revenue FLOAT64,
  customer_tier STRING,  -- enterprise, mid-market, smb

  -- Status
  lifecycle_stage STRING,  -- lead, mql, sql, customer, churned
  customer_status STRING,  -- active, inactive, churned
  is_customer BOOLEAN,

  -- Value metrics
  total_revenue FLOAT64,
  total_orders INT64,
  average_order_value FLOAT64,
  lifetime_value FLOAT64,
  predicted_clv FLOAT64,  -- From ML model

  -- Engagement scores
  lead_score FLOAT64,  -- From ML model
  engagement_score FLOAT64,
  email_engagement_score FLOAT64,
  web_engagement_score FLOAT64,
  product_engagement_score FLOAT64,

  -- Risk indicators
  churn_risk_score FLOAT64,  -- From ML model
  churn_risk_category STRING,  -- low, medium, high

  -- Acquisition
  acquisition_date DATE,
  acquisition_source STRING,
  acquisition_medium STRING,
  acquisition_campaign STRING,
  first_touch_channel STRING,
  last_touch_channel STRING,

  -- Activity timestamps
  first_seen_date DATE,
  last_seen_date DATE,
  last_purchase_date DATE,
  last_email_open_date DATE,
  last_web_visit_date DATE,
  last_support_ticket_date DATE,

  -- Preferences
  email_opt_in BOOLEAN,
  sms_opt_in BOOLEAN,
  preferred_communication_channel STRING,

  -- Support
  total_support_tickets INT64,
  open_support_tickets INT64,
  average_ticket_resolution_hours FLOAT64,
  satisfaction_score FLOAT64,

  -- Metadata
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

  -- Data quality flags
  email_is_valid BOOLEAN,
  phone_is_valid BOOLEAN,
  address_is_complete BOOLEAN,
  profile_completeness_score FLOAT64  -- 0-100
)
PARTITION BY DATE(last_seen_date)
CLUSTER BY customer_tier, lifecycle_stage, is_customer
OPTIONS(
  description="Unified customer 360 view - single source of truth for all customer data"
);

-- ============================================================
-- 2. STAGING: LEADS
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.leads` (
  lead_id STRING NOT NULL,
  customer_id STRING,  -- Links to customer_360

  -- Lead details
  email STRING,
  first_name STRING,
  last_name STRING,
  company STRING,
  title STRING,
  phone STRING,

  -- Lead attributes
  status STRING,  -- new, contacted, qualified, converted, disqualified
  lead_source STRING,
  lead_source_detail STRING,
  rating STRING,  -- hot, warm, cold

  -- Scores
  lead_score FLOAT64,  -- ML-generated
  engagement_score FLOAT64,

  -- Product interest
  product_interest STRING,
  use_case STRING,
  pain_points ARRAY<STRING>,

  -- Qualification
  budget STRING,  -- <10k, 10k-50k, 50k-100k, 100k+
  authority STRING,  -- decision_maker, influencer, user
  need_urgency STRING,  -- immediate, 3_months, 6_months, exploring
  timeline STRING,

  -- Activity
  total_page_views INT64,
  total_email_opens INT64,
  total_email_clicks INT64,
  total_content_downloads INT64,
  last_activity_date DATE,

  -- Conversion
  is_converted BOOLEAN,
  converted_date DATE,
  converted_account_id STRING,
  converted_opportunity_id STRING,

  -- Assignment
  owner_id STRING,
  owner_name STRING,

  -- Timestamps
  created_date DATE,
  last_modified_date DATE,
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY created_date
CLUSTER BY status, lead_source, is_converted
OPTIONS(
  description="Cleaned and enriched leads data"
);

-- ============================================================
-- 3. STAGING: WEB EVENTS (Unified Digital Behavior)
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.web_events` (
  event_id STRING NOT NULL,
  event_timestamp TIMESTAMP,
  event_date DATE,

  -- User identification
  user_id STRING,
  customer_id STRING,
  session_id STRING,

  -- Event details
  event_type STRING,  -- page_view, button_click, form_submit, video_play, etc.
  event_category STRING,
  event_action STRING,
  event_label STRING,
  event_value FLOAT64,

  -- Page context
  page_url STRING,
  page_path STRING,
  page_title STRING,
  page_hostname STRING,
  referrer_url STRING,

  -- Traffic source
  utm_source STRING,
  utm_medium STRING,
  utm_campaign STRING,
  utm_content STRING,
  utm_term STRING,

  -- Device
  device_category STRING,  -- desktop, mobile, tablet
  device_type STRING,
  browser STRING,
  operating_system STRING,

  -- Geography
  country STRING,
  region STRING,
  city STRING,

  -- Session context
  is_new_session BOOLEAN,
  session_number INT64,
  time_on_page_seconds INT64,

  -- Data source
  source_system STRING,  -- ga360, firebase

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY event_date
CLUSTER BY event_type, customer_id, event_date
OPTIONS(
  description="Unified web and app events from GA360 and Firebase"
);

-- ============================================================
-- 4. STAGING: EMAIL ENGAGEMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.email_engagement` (
  event_id STRING NOT NULL,
  event_timestamp TIMESTAMP,
  event_date DATE,

  -- User
  customer_id STRING,
  email_address STRING,

  -- Campaign
  campaign_id STRING,
  campaign_name STRING,
  campaign_type STRING,  -- promotional, transactional, nurture

  -- Email details
  subject_line STRING,
  send_id STRING,
  message_variation_id STRING,

  -- Event type
  event_type STRING,  -- sent, delivered, opened, clicked, bounced, unsubscribed, complained

  -- Click details (for click events)
  link_url STRING,
  link_position INT64,

  -- Bounce details (for bounce events)
  bounce_type STRING,  -- hard, soft
  bounce_reason STRING,

  -- Timing
  time_to_open_minutes INT64,
  time_to_click_minutes INT64,

  -- Device (if tracked)
  device_type STRING,
  email_client STRING,

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY event_date
CLUSTER BY event_type, campaign_id, customer_id
OPTIONS(
  description="Unified email engagement events from Braze"
);

-- ============================================================
-- 5. STAGING: TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.transactions` (
  transaction_id STRING NOT NULL,
  customer_id STRING,

  -- Transaction details
  transaction_date DATE,
  transaction_timestamp TIMESTAMP,
  order_number STRING,

  -- Amounts
  revenue FLOAT64,
  tax FLOAT64,
  shipping FLOAT64,
  discount FLOAT64,
  net_revenue FLOAT64,  -- revenue - discount
  profit FLOAT64,  -- if available

  -- Currency
  currency STRING,
  revenue_usd FLOAT64,  -- Standardized to USD

  -- Products
  product_count INT64,
  total_quantity INT64,
  product_categories ARRAY<STRING>,

  -- Status
  financial_status STRING,  -- paid, pending, refunded
  fulfillment_status STRING,  -- fulfilled, partial, unfulfilled

  -- Attribution
  traffic_source STRING,
  traffic_medium STRING,
  campaign STRING,
  first_touch_channel STRING,
  last_touch_channel STRING,

  -- Customer context
  is_first_purchase BOOLEAN,
  customer_purchase_number INT64,
  days_since_last_purchase INT64,

  -- Platform
  source_system STRING,  -- shopify, ga360

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY transaction_date
CLUSTER BY customer_id, is_first_purchase
OPTIONS(
  description="Unified transaction data from all e-commerce platforms"
);

-- ============================================================
-- 6. STAGING: AD PERFORMANCE
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.ad_performance` (
  -- Unique identifier
  performance_id STRING NOT NULL,
  date DATE,

  -- Campaign hierarchy
  platform STRING,  -- google_ads, facebook, linkedin
  account_id STRING,
  campaign_id STRING,
  campaign_name STRING,
  ad_group_id STRING,
  ad_group_name STRING,
  ad_id STRING,
  ad_name STRING,

  -- Campaign attributes
  campaign_type STRING,
  campaign_objective STRING,
  budget_daily FLOAT64,

  -- Creative
  ad_headline STRING,
  ad_description STRING,
  ad_url STRING,

  -- Metrics
  impressions INT64,
  clicks INT64,
  cost FLOAT64,
  conversions FLOAT64,
  conversion_value FLOAT64,

  -- Calculated metrics
  ctr FLOAT64,  -- Click-through rate
  cpc FLOAT64,  -- Cost per click
  cpm FLOAT64,  -- Cost per thousand impressions
  cpa FLOAT64,  -- Cost per acquisition
  roas FLOAT64,  -- Return on ad spend

  -- Quality metrics
  quality_score INT64,
  relevance_score FLOAT64,

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY platform, campaign_id, date
OPTIONS(
  description="Unified advertising performance across all platforms"
);

-- ============================================================
-- 7. STAGING: SUPPORT INTERACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.support_tickets` (
  ticket_id INT64 NOT NULL,
  customer_id STRING,

  -- Ticket details
  subject STRING,
  description STRING,
  status STRING,  -- new, open, pending, solved, closed
  priority STRING,  -- low, medium, high, urgent
  type STRING,  -- question, incident, problem, task

  -- Assignment
  assignee_id INT64,
  assignee_name STRING,
  group_name STRING,

  -- Timing
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  solved_at TIMESTAMP,
  closed_at TIMESTAMP,

  -- SLA
  time_to_first_response_minutes INT64,
  time_to_resolution_hours FLOAT64,
  sla_breached BOOLEAN,

  -- Categories
  tags ARRAY<STRING>,
  category STRING,  -- Derived from tags
  subcategory STRING,

  -- Satisfaction
  satisfaction_rating STRING,  -- good, bad
  satisfaction_score FLOAT64,  -- 0-100
  satisfaction_comment STRING,

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY status, priority, customer_id
OPTIONS(
  description="Cleaned support ticket data from Zendesk"
);

-- ============================================================
-- 8. STAGING: PRODUCT CATALOG
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.products` (
  product_id STRING NOT NULL,

  -- Product details
  product_name STRING,
  product_title STRING,
  product_description STRING,
  sku STRING,

  -- Categorization
  product_category STRING,
  product_subcategory STRING,
  product_type STRING,
  brand STRING,

  -- Pricing
  price FLOAT64,
  compare_at_price FLOAT64,
  cost FLOAT64,
  margin FLOAT64,

  -- Inventory
  inventory_quantity INT64,
  inventory_policy STRING,

  -- Attributes
  tags ARRAY<STRING>,
  is_active BOOLEAN,
  is_featured BOOLEAN,

  -- Performance indicators
  total_orders_30d INT64,
  total_revenue_30d FLOAT64,
  average_rating FLOAT64,

  -- Metadata
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY product_category, is_active
OPTIONS(
  description="Product catalog from e-commerce platforms"
);

-- ============================================================
-- STAGING DATA QUALITY CHECKS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.staging.data_quality_checks` (
  check_id STRING NOT NULL,
  check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  target_table STRING,
  check_type STRING,
  check_status STRING,

  -- Test details
  test_name STRING,
  test_query STRING,
  expected_result STRING,
  actual_result STRING,

  -- Thresholds
  warning_threshold FLOAT64,
  error_threshold FLOAT64,
  actual_value FLOAT64,

  -- Actions taken
  alert_sent BOOLEAN,
  dbt_run_halted BOOLEAN,

  -- Context
  dbt_run_id STRING,
  dbt_model_name STRING
)
PARTITION BY DATE(check_timestamp)
OPTIONS(
  description="Data quality test results for Silver layer"
);

-- ============================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================

-- Active customers view
CREATE OR REPLACE VIEW `nexvigilant-marketing-prod.staging.v_active_customers` AS
SELECT *
FROM `nexvigilant-marketing-prod.staging.customer_360`
WHERE customer_status = 'active'
  AND is_customer = TRUE
  AND last_seen_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);

-- High-value leads view
CREATE OR REPLACE VIEW `nexvigilant-marketing-prod.staging.v_high_value_leads` AS
SELECT *
FROM `nexvigilant-marketing-prod.staging.leads`
WHERE lead_score >= 70
  AND status IN ('new', 'contacted', 'qualified')
  AND is_converted = FALSE;

-- Churn risk customers view
CREATE OR REPLACE VIEW `nexvigilant-marketing-prod.staging.v_churn_risk_customers` AS
SELECT *
FROM `nexvigilant-marketing-prod.staging.customer_360`
WHERE churn_risk_category IN ('medium', 'high')
  AND is_customer = TRUE
  AND customer_status = 'active';
