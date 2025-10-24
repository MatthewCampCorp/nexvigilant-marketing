-- ============================================================
-- BRONZE LAYER: Raw Data Schemas
-- ============================================================
-- Purpose: Ingest raw data from source systems with minimal transformation
-- Strategy: Land data exactly as received, partition by date for cost optimization
-- Data Quality: Basic schema validation only, no business logic
-- Retention: 90 days (compliance requirement)
-- ============================================================

-- Project and dataset configuration
-- Project: nexvigilant-marketing-prod
-- Dataset: raw_data (Bronze layer)

-- ============================================================
-- 1. SALESFORCE CRM DATA
-- ============================================================

-- Raw Leads from Salesforce
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.salesforce_leads` (
  -- Salesforce Standard Fields
  id STRING NOT NULL,
  first_name STRING,
  last_name STRING,
  email STRING,
  phone STRING,
  company STRING,
  title STRING,
  industry STRING,
  status STRING,
  lead_source STRING,
  rating STRING,

  -- Custom Fields (adapt to your Salesforce org)
  product_interest__c STRING,
  lead_score__c FLOAT64,
  engagement_score__c FLOAT64,
  last_activity_date__c TIMESTAMP,

  -- Metadata
  created_date TIMESTAMP,
  last_modified_date TIMESTAMP,
  is_converted BOOLEAN,
  converted_account_id STRING,
  converted_contact_id STRING,
  converted_opportunity_id STRING,

  -- Audit fields
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(_fivetran_synced)
CLUSTER BY status, lead_source
OPTIONS(
  description="Raw leads data from Salesforce CRM",
  require_partition_filter=true
);

-- Raw Accounts from Salesforce
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.salesforce_accounts` (
  id STRING NOT NULL,
  name STRING,
  type STRING,
  industry STRING,
  annual_revenue FLOAT64,
  number_of_employees INT64,
  billing_street STRING,
  billing_city STRING,
  billing_state STRING,
  billing_country STRING,
  billing_postal_code STRING,

  -- Custom fields
  customer_tier__c STRING,
  account_health_score__c FLOAT64,
  mrr__c FLOAT64,
  arr__c FLOAT64,

  -- Metadata
  created_date TIMESTAMP,
  last_modified_date TIMESTAMP,
  owner_id STRING,

  -- Audit
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(_fivetran_synced)
CLUSTER BY type, industry
OPTIONS(
  description="Raw accounts data from Salesforce CRM"
);

-- Raw Opportunities from Salesforce
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.salesforce_opportunities` (
  id STRING NOT NULL,
  account_id STRING,
  name STRING,
  stage_name STRING,
  amount FLOAT64,
  probability FLOAT64,
  close_date DATE,
  type STRING,
  lead_source STRING,

  -- Tracking
  created_date TIMESTAMP,
  last_modified_date TIMESTAMP,
  is_won BOOLEAN,
  is_closed BOOLEAN,
  forecast_category STRING,

  -- Audit
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(_fivetran_synced)
CLUSTER BY stage_name, close_date
OPTIONS(
  description="Raw opportunities data from Salesforce CRM"
);

-- ============================================================
-- 2. GOOGLE ANALYTICS 360 DATA
-- ============================================================

-- Raw GA360 Sessions (daily export)
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.ga360_sessions` (
  -- Session identifiers
  full_visitor_id STRING,
  visit_id INT64,
  visit_start_time TIMESTAMP,

  -- Traffic source
  traffic_source_source STRING,
  traffic_source_medium STRING,
  traffic_source_campaign STRING,
  traffic_source_keyword STRING,

  -- Device
  device_category STRING,
  device_browser STRING,
  device_operating_system STRING,

  -- Geography
  geo_country STRING,
  geo_region STRING,
  geo_city STRING,

  -- Session metrics
  totals_visits INT64,
  totals_hits INT64,
  totals_pageviews INT64,
  totals_time_on_site INT64,
  totals_bounces INT64,
  totals_transactions INT64,
  totals_transaction_revenue FLOAT64,

  -- Custom dimensions (adapt to your GA360 setup)
  custom_dimension_user_id STRING,
  custom_dimension_customer_tier STRING,

  -- Audit
  _table_suffix STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(visit_start_time)
CLUSTER BY full_visitor_id, traffic_source_medium
OPTIONS(
  description="Raw session data from Google Analytics 360"
);

-- Raw GA360 Events
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.ga360_events` (
  full_visitor_id STRING,
  visit_id INT64,
  hit_number INT64,
  hit_time TIMESTAMP,
  hit_type STRING,

  -- Page tracking
  page_path STRING,
  page_title STRING,
  page_hostname STRING,

  -- Event tracking
  event_category STRING,
  event_action STRING,
  event_label STRING,
  event_value INT64,

  -- E-commerce (if applicable)
  transaction_id STRING,
  transaction_revenue FLOAT64,
  product_name STRING,
  product_category STRING,
  product_quantity INT64,

  -- Audit
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(hit_time)
CLUSTER BY event_category, full_visitor_id
OPTIONS(
  description="Raw event-level data from Google Analytics 360"
);

-- ============================================================
-- 3. FIREBASE (Mobile App Analytics)
-- ============================================================

-- Raw Firebase Events
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.firebase_events` (
  event_date DATE,
  event_timestamp INT64,
  event_name STRING,
  event_params ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,

  -- User identifiers
  user_id STRING,
  user_pseudo_id STRING,

  -- User properties
  user_properties ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,

  -- Device
  device_category STRING,
  device_mobile_brand_name STRING,
  device_mobile_model_name STRING,
  device_operating_system STRING,
  device_operating_system_version STRING,

  -- App info
  app_info_id STRING,
  app_info_version STRING,

  -- Geography
  geo_country STRING,
  geo_region STRING,
  geo_city STRING,

  -- Platform
  platform STRING,
  stream_id STRING,

  -- Audit
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY event_date
CLUSTER BY event_name, user_pseudo_id
OPTIONS(
  description="Raw event data from Firebase Analytics"
);

-- ============================================================
-- 4. GOOGLE ADS DATA
-- ============================================================

-- Raw Google Ads Campaign Performance
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.google_ads_campaigns` (
  date DATE,
  customer_id INT64,
  campaign_id INT64,
  campaign_name STRING,
  campaign_status STRING,
  campaign_type STRING,

  -- Metrics
  impressions INT64,
  clicks INT64,
  cost_micros INT64,  -- Cost in micros (divide by 1,000,000 for actual cost)
  conversions FLOAT64,
  conversion_value FLOAT64,

  -- Performance
  ctr FLOAT64,  -- Click-through rate
  average_cpc FLOAT64,  -- Average cost per click
  average_cpm FLOAT64,  -- Average cost per thousand impressions

  -- Audit
  _fivetran_synced TIMESTAMP,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY campaign_id, date
OPTIONS(
  description="Raw campaign performance data from Google Ads"
);

-- Raw Google Ads Keywords
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.google_ads_keywords` (
  date DATE,
  customer_id INT64,
  campaign_id INT64,
  ad_group_id INT64,
  keyword_id INT64,
  keyword_text STRING,
  keyword_match_type STRING,

  -- Metrics
  impressions INT64,
  clicks INT64,
  cost_micros INT64,
  conversions FLOAT64,

  -- Quality score
  quality_score INT64,

  -- Audit
  _fivetran_synced TIMESTAMP,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY campaign_id, keyword_id
OPTIONS(
  description="Raw keyword performance data from Google Ads"
);

-- ============================================================
-- 5. BRAZE (Customer Engagement Platform)
-- ============================================================

-- Raw Braze Email Sends
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.braze_email_sends` (
  id STRING,
  user_id STRING,
  external_user_id STRING,
  email_address STRING,

  -- Campaign info
  campaign_id STRING,
  campaign_name STRING,
  canvas_id STRING,
  canvas_name STRING,
  canvas_step_id STRING,

  -- Message details
  message_variation_id STRING,
  send_id STRING,

  -- Timing
  time TIMESTAMP,
  timezone STRING,

  -- Audit
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(time)
CLUSTER BY campaign_id, user_id
OPTIONS(
  description="Raw email send events from Braze"
);

-- Raw Braze Email Events (opens, clicks, etc.)
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.braze_email_events` (
  id STRING,
  user_id STRING,
  external_user_id STRING,
  email_address STRING,

  -- Event type
  event_type STRING,  -- open, click, bounce, unsubscribe, etc.

  -- Campaign info
  campaign_id STRING,
  send_id STRING,

  -- Event details
  link_url STRING,  -- For click events
  bounce_reason STRING,  -- For bounce events

  -- Timing
  time TIMESTAMP,

  -- Audit
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(time)
CLUSTER BY event_type, campaign_id
OPTIONS(
  description="Raw email engagement events from Braze"
);

-- ============================================================
-- 6. SHOPIFY (E-commerce Platform)
-- ============================================================

-- Raw Shopify Orders
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.shopify_orders` (
  id INT64,
  order_number INT64,
  email STRING,
  customer_id INT64,

  -- Order details
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  financial_status STRING,
  fulfillment_status STRING,

  -- Amounts
  total_price FLOAT64,
  subtotal_price FLOAT64,
  total_tax FLOAT64,
  total_discounts FLOAT64,
  total_shipping FLOAT64,

  -- Currency
  currency STRING,

  -- Source
  source_name STRING,
  referring_site STRING,
  landing_site STRING,

  -- Audit
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY customer_id, financial_status
OPTIONS(
  description="Raw order data from Shopify"
);

-- Raw Shopify Order Line Items
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.shopify_order_line_items` (
  id INT64,
  order_id INT64,
  product_id INT64,
  variant_id INT64,

  -- Product details
  name STRING,
  title STRING,
  sku STRING,

  -- Quantities and pricing
  quantity INT64,
  price FLOAT64,
  total_discount FLOAT64,

  -- Audit
  _fivetran_synced TIMESTAMP,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(_fivetran_synced)
CLUSTER BY order_id, product_id
OPTIONS(
  description="Raw order line items from Shopify"
);

-- ============================================================
-- 7. ZENDESK (Customer Support)
-- ============================================================

-- Raw Zendesk Tickets
CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.zendesk_tickets` (
  id INT64,
  requester_id INT64,
  assignee_id INT64,
  organization_id INT64,

  -- Ticket details
  subject STRING,
  description STRING,
  status STRING,
  priority STRING,
  type STRING,

  -- Timing
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  solved_at TIMESTAMP,

  -- Tags
  tags ARRAY<STRING>,

  -- Satisfaction
  satisfaction_rating_score STRING,
  satisfaction_rating_comment STRING,

  -- Audit
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY status, priority
OPTIONS(
  description="Raw support ticket data from Zendesk"
);

-- ============================================================
-- DATA QUALITY MONITORING TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.raw_data.data_quality_checks` (
  check_id STRING NOT NULL,
  check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  source_table STRING,
  check_type STRING,  -- freshness, null_rate, row_count, schema_validation
  check_status STRING,  -- passed, warning, failed

  -- Metrics
  expected_value FLOAT64,
  actual_value FLOAT64,
  threshold_value FLOAT64,

  -- Details
  failure_reason STRING,
  rows_affected INT64,

  -- Actions
  alert_sent BOOLEAN,
  pipeline_halted BOOLEAN
)
PARTITION BY DATE(check_timestamp)
OPTIONS(
  description="Data quality check results for Bronze layer"
);

-- ============================================================
-- INDEXES AND PERMISSIONS
-- ============================================================

-- Note: BigQuery uses clustering instead of traditional indexes
-- Clustering columns are defined in table OPTIONS above

-- Grant permissions (execute after tables are created)
-- GRANT `roles/bigquery.dataViewer` ON TABLE `raw_data.*` TO 'serviceAccount:etl@nexvigilant-marketing-prod.iam.gserviceaccount.com';
-- GRANT `roles/bigquery.dataEditor` ON TABLE `raw_data.*` TO 'serviceAccount:fivetran@nexvigilant-marketing-prod.iam.gserviceaccount.com';
