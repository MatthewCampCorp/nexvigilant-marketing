-- ============================================================
-- GOLD LAYER: Business Logic / Data Marts
-- ============================================================
-- Purpose: Optimized analytical tables for specific business use cases
-- Strategy: Pre-aggregated, denormalized, business-ready datasets
-- Data Quality: Highest - ready for executive dashboards and ML models
-- Retention: 2 years
-- ============================================================

-- Project: nexvigilant-marketing-prod
-- Dataset: marts (Gold layer)

-- ============================================================
-- 1. MARKETING ATTRIBUTION MART
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.marketing_attribution` (
  attribution_id STRING NOT NULL,
  customer_id STRING,
  transaction_id STRING,
  transaction_date DATE,
  revenue FLOAT64,

  -- First-touch attribution
  first_touch_channel STRING,
  first_touch_source STRING,
  first_touch_medium STRING,
  first_touch_campaign STRING,
  first_touch_date DATE,
  first_touch_revenue FLOAT64,  -- Revenue attributed to first touch

  -- Last-touch attribution
  last_touch_channel STRING,
  last_touch_source STRING,
  last_touch_medium STRING,
  last_touch_campaign STRING,
  last_touch_date DATE,
  last_touch_revenue FLOAT64,  -- Revenue attributed to last touch

  -- Linear attribution (equal credit to all touchpoints)
  touchpoint_count INT64,
  linear_attribution_revenue FLOAT64,

  -- Time-decay attribution (more recent touches get more credit)
  time_decay_revenue FLOAT64,

  -- U-shaped attribution (40% first, 40% last, 20% middle)
  u_shaped_revenue FLOAT64,

  -- Multi-touch journey
  journey_touchpoints ARRAY<STRUCT<
    channel STRING,
    source STRING,
    medium STRING,
    campaign STRING,
    touchpoint_date DATE,
    position_in_journey INT64
  >>,

  -- Customer context
  is_first_purchase BOOLEAN,
  customer_lifetime_value FLOAT64,
  days_to_conversion INT64,  -- From first touch to conversion

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY transaction_date
CLUSTER BY first_touch_channel, last_touch_channel
OPTIONS(
  description="Multi-touch attribution analysis for marketing performance"
);

-- ============================================================
-- 2. CUSTOMER COHORT ANALYSIS MART
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.customer_cohorts` (
  cohort_month DATE,  -- First purchase month
  months_since_cohort INT64,  -- 0, 1, 2, 3...
  analysis_month DATE,  -- The month being analyzed

  -- Cohort size
  cohort_size INT64,  -- Total customers in this cohort
  active_customers INT64,  -- Still active in analysis_month
  churned_customers INT64,

  -- Retention metrics
  retention_rate FLOAT64,  -- % still active
  churn_rate FLOAT64,  -- % churned

  -- Revenue metrics
  cohort_revenue FLOAT64,
  average_revenue_per_user FLOAT64,
  cumulative_revenue FLOAT64,

  -- Engagement metrics
  average_orders_per_customer FLOAT64,
  average_order_frequency_days FLOAT64,
  repeat_purchase_rate FLOAT64,

  -- CLV metrics
  actual_ltv FLOAT64,  -- Actual lifetime value so far
  projected_ltv FLOAT64,  -- ML-predicted lifetime value

  -- Cohort characteristics
  primary_acquisition_channel STRING,
  primary_customer_tier STRING,

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY cohort_month
CLUSTER BY cohort_month, months_since_cohort
OPTIONS(
  description="Customer cohort retention and LTV analysis"
);

-- ============================================================
-- 3. CAMPAIGN PERFORMANCE MART
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.campaign_performance` (
  campaign_id STRING NOT NULL,
  campaign_date DATE,
  campaign_name STRING,
  campaign_type STRING,  -- email, paid_search, paid_social, display
  platform STRING,  -- braze, google_ads, facebook, etc.

  -- Spend
  campaign_spend FLOAT64,
  budget_daily FLOAT64,
  budget_total FLOAT64,
  budget_utilization_rate FLOAT64,

  -- Impressions & Reach
  impressions INT64,
  unique_reach INT64,
  frequency FLOAT64,  -- Impressions / Reach

  -- Engagement
  clicks INT64,
  email_opens INT64,
  email_clicks INT64,
  video_views INT64,
  social_engagements INT64,

  -- Conversion funnel
  landing_page_visits INT64,
  form_submissions INT64,
  leads_generated INT64,
  mqls_generated INT64,
  sqls_generated INT64,
  opportunities_created INT64,
  closed_won_deals INT64,

  -- Conversion rates
  ctr FLOAT64,  -- Click-through rate
  conversion_rate FLOAT64,  -- Clicks to conversions
  lead_conversion_rate FLOAT64,  -- Leads to customers
  mql_to_sql_rate FLOAT64,
  sql_to_opportunity_rate FLOAT64,
  win_rate FLOAT64,  -- Opportunities to closed won

  -- Financial metrics
  revenue FLOAT64,
  pipeline_value FLOAT64,  -- Opportunity value generated
  cost_per_click FLOAT64,
  cost_per_lead FLOAT64,
  cost_per_mql FLOAT64,
  cost_per_sql FLOAT64,
  cost_per_customer FLOAT64,
  roas FLOAT64,  -- Return on ad spend
  roi FLOAT64,  -- Return on investment

  -- Efficiency scores
  efficiency_score FLOAT64,  -- Composite 0-100 score
  quality_score FLOAT64,  -- Platform-specific quality score

  -- Targets vs actuals
  target_impressions INT64,
  target_clicks INT64,
  target_conversions INT64,
  target_roas FLOAT64,
  impressions_vs_target_pct FLOAT64,
  clicks_vs_target_pct FLOAT64,
  conversions_vs_target_pct FLOAT64,
  roas_vs_target_pct FLOAT64,

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY campaign_date
CLUSTER BY platform, campaign_type, campaign_date
OPTIONS(
  description="Comprehensive campaign performance metrics and ROI analysis"
);

-- ============================================================
-- 4. PRODUCT PERFORMANCE MART
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.product_performance` (
  product_id STRING NOT NULL,
  analysis_date DATE,
  product_name STRING,
  product_category STRING,
  brand STRING,

  -- Sales metrics (30-day rolling)
  orders_30d INT64,
  revenue_30d FLOAT64,
  units_sold_30d INT64,
  unique_customers_30d INT64,

  -- Sales metrics (90-day rolling)
  orders_90d INT64,
  revenue_90d FLOAT64,
  units_sold_90d INT64,
  unique_customers_90d INT64,

  -- Pricing
  current_price FLOAT64,
  average_selling_price_30d FLOAT64,
  discount_rate_30d FLOAT64,

  -- Profitability
  cost FLOAT64,
  margin FLOAT64,
  total_profit_30d FLOAT64,
  profit_margin_pct FLOAT64,

  -- Customer behavior
  average_quantity_per_order FLOAT64,
  repeat_purchase_rate_30d FLOAT64,
  cross_sell_rate FLOAT64,
  return_rate FLOAT64,

  -- Marketing
  paid_traffic_orders INT64,
  organic_traffic_orders INT64,
  ad_spend_allocated_30d FLOAT64,
  roas_30d FLOAT64,

  -- Inventory
  current_inventory INT64,
  days_of_inventory_remaining INT64,
  stockout_days_30d INT64,

  -- Trends
  revenue_growth_mom FLOAT64,  -- Month-over-month
  revenue_growth_yoy FLOAT64,  -- Year-over-year
  trend_direction STRING,  -- growing, declining, stable

  -- Rankings
  category_revenue_rank INT64,
  overall_revenue_rank INT64,

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY analysis_date
CLUSTER BY product_category, analysis_date
OPTIONS(
  description="Product-level performance metrics and trends"
);

-- ============================================================
-- 5. CUSTOMER HEALTH SCORE MART
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.customer_health_scores` (
  customer_id STRING NOT NULL,
  score_date DATE,

  -- Overall health score (0-100)
  health_score FLOAT64,
  health_category STRING,  -- excellent, good, fair, at_risk, critical

  -- Component scores (each 0-100)
  usage_score FLOAT64,  -- Product engagement
  financial_score FLOAT64,  -- Revenue trends
  support_score FLOAT64,  -- Support interactions
  engagement_score FLOAT64,  -- Marketing engagement
  sentiment_score FLOAT64,  -- Surveys, NPS

  -- Usage metrics
  days_since_last_login INT64,
  logins_30d INT64,
  feature_adoption_rate FLOAT64,
  power_user_actions_30d INT64,

  -- Financial metrics
  revenue_30d FLOAT64,
  revenue_90d FLOAT64,
  revenue_trend STRING,  -- growing, declining, stable
  payment_issues_90d INT64,
  days_since_last_purchase INT64,

  -- Support metrics
  open_tickets INT64,
  tickets_30d INT64,
  average_satisfaction_score FLOAT64,
  escalations_90d INT64,

  -- Engagement metrics
  email_engagement_rate FLOAT64,
  web_visits_30d INT64,
  content_downloads_30d INT64,

  -- Risk indicators
  churn_risk_score FLOAT64,
  churn_probability FLOAT64,  -- From ML model
  risk_factors ARRAY<STRING>,
  early_warning_signals ARRAY<STRING>,

  -- Opportunities
  upsell_score FLOAT64,
  cross_sell_opportunities ARRAY<STRING>,
  expansion_revenue_potential FLOAT64,

  -- Actions & alerts
  recommended_actions ARRAY<STRING>,
  alert_triggered BOOLEAN,
  alert_priority STRING,  -- low, medium, high, critical

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY score_date
CLUSTER BY health_category, churn_risk_score DESC
OPTIONS(
  description="Customer health scores with early warning system for churn"
);

-- ============================================================
-- 6. LEAD SCORING & QUALIFICATION MART
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.lead_scores` (
  lead_id STRING NOT NULL,
  score_date DATE,
  customer_id STRING,

  -- Overall lead score (0-100, ML-generated)
  lead_score FLOAT64,
  lead_grade STRING,  -- A+, A, B, C, D, F
  qualification_status STRING,  -- mql, sql, not_qualified

  -- Score components
  demographic_score FLOAT64,  -- Title, company size, industry fit
  firmographic_score FLOAT64,  -- Company attributes
  behavioral_score FLOAT64,  -- Web activity, email engagement
  intent_score FLOAT64,  -- Product interest signals

  -- Behavioral signals (30 days)
  page_views_30d INT64,
  unique_pages_30d INT64,
  time_on_site_minutes_30d FLOAT64,
  visits_30d INT64,
  email_opens_30d INT64,
  email_clicks_30d INT64,
  content_downloads_30d INT64,
  webinar_registrations_30d INT64,
  demo_requests_30d INT64,

  -- Intent signals
  pricing_page_views INT64,
  competitor_research BOOLEAN,
  high_intent_keywords ARRAY<STRING>,
  case_study_views INT64,

  -- BANT qualification
  budget_qualified BOOLEAN,
  authority_qualified BOOLEAN,
  need_qualified BOOLEAN,
  timeline_qualified BOOLEAN,
  bant_score FLOAT64,  -- 0-4 (how many BANT criteria met)

  -- Fit scores
  icp_fit_score FLOAT64,  -- Ideal customer profile match
  product_fit_score FLOAT64,
  use_case_fit_score FLOAT64,

  -- Conversion predictions
  conversion_probability FLOAT64,  -- ML-predicted
  predicted_deal_size FLOAT64,
  predicted_time_to_close_days INT64,

  -- Recommendations
  recommended_next_action STRING,
  recommended_content ARRAY<STRING>,
  sales_readiness_score FLOAT64,  -- Ready to hand off to sales?

  -- Context
  lead_source STRING,
  lead_age_days INT64,
  days_since_last_activity INT64,

  -- Metadata
  model_version STRING,  -- ML model version used
  prediction_confidence FLOAT64,
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY score_date
CLUSTER BY lead_score DESC, qualification_status
OPTIONS(
  description="ML-powered lead scoring and qualification with actionable recommendations"
);

-- ============================================================
-- 7. EXECUTIVE KPI DASHBOARD MART
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.executive_kpis` (
  kpi_date DATE,
  kpi_category STRING,  -- marketing, sales, customer_success, product
  kpi_name STRING,
  kpi_value FLOAT64,
  kpi_unit STRING,  -- dollars, percent, count, days

  -- Targets
  target_value FLOAT64,
  variance FLOAT64,  -- Actual vs target
  variance_pct FLOAT64,
  is_on_target BOOLEAN,

  -- Trends
  previous_period_value FLOAT64,
  period_over_period_change FLOAT64,
  period_over_period_change_pct FLOAT64,
  trend_direction STRING,  -- up, down, flat

  -- Context
  period_type STRING,  -- daily, weekly, monthly, quarterly
  fiscal_year INT64,
  fiscal_quarter STRING,
  fiscal_month STRING,

  -- Metadata
  data_freshness_hours FLOAT64,
  calculation_method STRING,
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY kpi_date
CLUSTER BY kpi_category, kpi_name
OPTIONS(
  description="Executive KPI dashboard with targets and trends"
);

-- Example KPIs tracked:
-- Marketing: CAC, MQL volume, conversion rates, ROAS, pipeline generated
-- Sales: Win rate, average deal size, sales cycle length, quota attainment
-- Customer Success: NRR, GRR, churn rate, NPS, expansion revenue
-- Product: MAU, DAU, feature adoption, time to value

-- ============================================================
-- 8. ML FEATURES MART (for Model Training)
-- ============================================================

CREATE TABLE IF NOT EXISTS `nexvigilant-marketing-prod.marts.ml_features` (
  feature_set_id STRING NOT NULL,
  entity_id STRING,  -- customer_id or lead_id
  entity_type STRING,  -- customer or lead
  snapshot_date DATE,

  -- Demographics (10 features)
  industry STRING,
  company_size_bucket STRING,
  title_level STRING,
  country STRING,
  account_age_days INT64,

  -- Behavioral (20 features)
  page_views_7d INT64,
  page_views_30d INT64,
  unique_pages_7d INT64,
  visits_7d INT64,
  visits_30d INT64,
  avg_session_duration_7d FLOAT64,
  email_opens_7d INT64,
  email_opens_30d INT64,
  email_clicks_7d INT64,
  email_clicks_30d INT64,
  content_downloads_30d INT64,
  days_since_last_visit INT64,
  days_since_last_email_open INT64,

  -- Engagement (10 features)
  engagement_score FLOAT64,
  recency_score FLOAT64,
  frequency_score FLOAT64,
  monetary_score FLOAT64,
  rfm_segment STRING,

  -- Financial (10 features)
  total_revenue FLOAT64,
  revenue_30d FLOAT64,
  revenue_90d FLOAT64,
  average_order_value FLOAT64,
  total_orders INT64,
  orders_30d INT64,
  days_since_last_purchase INT64,
  lifetime_value FLOAT64,

  -- Support (5 features)
  total_tickets INT64,
  tickets_30d INT64,
  open_tickets INT64,
  avg_satisfaction_score FLOAT64,
  escalations_90d INT64,

  -- Product usage (10 features, if applicable)
  login_frequency_7d FLOAT64,
  feature_adoption_score FLOAT64,
  power_user_score FLOAT64,
  api_calls_7d INT64,

  -- Target variables (for training)
  label_churned BOOLEAN,  -- Did they churn? (for churn prediction)
  label_converted BOOLEAN,  -- Did they convert? (for lead scoring)
  label_clv FLOAT64,  -- Actual CLV (for CLV prediction)
  label_next_purchase_days INT64,  -- Days until next purchase

  -- Metadata
  dbt_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY snapshot_date
CLUSTER BY entity_type, snapshot_date
OPTIONS(
  description="Feature store for ML model training and inference"
);

-- ============================================================
-- MATERIALIZED VIEWS FOR REAL-TIME DASHBOARDS
-- ============================================================

-- Real-time marketing spend
CREATE MATERIALIZED VIEW IF NOT EXISTS `nexvigilant-marketing-prod.marts.mv_marketing_spend_today` AS
SELECT
  DATE(CURRENT_DATE()) as spend_date,
  platform,
  SUM(campaign_spend) as total_spend,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks,
  SUM(conversions) as total_conversions,
  SAFE_DIVIDE(SUM(clicks), SUM(impressions)) as avg_ctr,
  SAFE_DIVIDE(SUM(campaign_spend), SUM(clicks)) as avg_cpc,
  SAFE_DIVIDE(SUM(revenue), SUM(campaign_spend)) as roas
FROM `nexvigilant-marketing-prod.marts.campaign_performance`
WHERE campaign_date = CURRENT_DATE()
GROUP BY platform;

-- Real-time customer health alerts
CREATE MATERIALIZED VIEW IF NOT EXISTS `nexvigilant-marketing-prod.marts.mv_health_alerts_active` AS
SELECT
  customer_id,
  health_score,
  health_category,
  churn_risk_score,
  risk_factors,
  recommended_actions,
  alert_priority
FROM `nexvigilant-marketing-prod.marts.customer_health_scores`
WHERE score_date = CURRENT_DATE()
  AND alert_triggered = TRUE
  AND health_category IN ('at_risk', 'critical')
ORDER BY churn_risk_score DESC;
