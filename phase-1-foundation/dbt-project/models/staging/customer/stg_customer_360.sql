{{
  config(
    materialized='table',
    partition_by={
      "field": "last_seen_date",
      "data_type": "date"
    },
    cluster_by=["customer_tier", "lifecycle_stage", "is_customer"],
    tags=["customer", "360", "daily"]
  )
}}

/*
============================================================
CUSTOMER 360: Unified Customer View
============================================================
Purpose: Create single source of truth for customer data
Strategy: Identity resolution + data unification from all sources
Dependencies: Salesforce, Shopify, GA360, Firebase, Braze
Refresh: Daily
Owner: Data Engineering
============================================================
*/

WITH salesforce_accounts AS (
  SELECT
    id AS salesforce_account_id,
    name AS company,
    industry,
    annual_revenue,
    number_of_employees AS company_size,
    billing_country AS country,
    billing_state AS state,
    billing_city AS city,
    billing_postal_code AS postal_code,
    customer_tier__c AS customer_tier,
    account_health_score__c AS health_score,
    mrr__c AS mrr,
    arr__c AS arr,
    created_date AS salesforce_created_date,
    last_modified_date AS salesforce_updated_date
  FROM {{ source('raw_data', 'salesforce_accounts') }}
  WHERE _fivetran_deleted = FALSE
),

salesforce_contacts AS (
  SELECT
    id AS salesforce_contact_id,
    account_id AS salesforce_account_id,
    email,
    first_name,
    last_name,
    CONCAT(first_name, ' ', last_name) AS full_name,
    phone,
    title,
    created_date,
    last_modified_date
  FROM {{ source('raw_data', 'salesforce_contacts') }}
  WHERE _fivetran_deleted = FALSE
    AND email IS NOT NULL
),

salesforce_leads AS (
  SELECT
    id AS salesforce_lead_id,
    email,
    first_name,
    last_name,
    company,
    title,
    status AS lead_status,
    lead_source,
    lead_score__c AS salesforce_lead_score,
    created_date AS lead_created_date,
    is_converted,
    converted_account_id,
    converted_contact_id
  FROM {{ source('raw_data', 'salesforce_leads') }}
  WHERE _fivetran_deleted = FALSE
    AND email IS NOT NULL
),

shopify_customers AS (
  SELECT
    id AS shopify_customer_id,
    email,
    first_name,
    last_name,
    total_spent AS shopify_lifetime_revenue,
    orders_count AS shopify_order_count,
    created_at AS shopify_created_date,
    updated_at AS shopify_updated_date
  FROM {{ source('raw_data', 'shopify_customers') }}
  WHERE _fivetran_deleted = FALSE
    AND email IS NOT NULL
),

ga360_users AS (
  SELECT
    user_id,
    custom_dimension_user_id AS ga360_user_id,
    MAX(visit_start_time) AS last_ga360_visit,
    MIN(visit_start_time) AS first_ga360_visit,
    COUNT(DISTINCT DATE(visit_start_time)) AS total_visit_days,
    SUM(totals_pageviews) AS total_pageviews,
    SUM(totals_time_on_site) AS total_time_on_site_seconds
  FROM {{ source('raw_data', 'ga360_sessions') }}
  WHERE custom_dimension_user_id IS NOT NULL
  GROUP BY 1, 2
),

firebase_users AS (
  SELECT
    user_id AS firebase_user_id,
    MAX(event_date) AS last_firebase_event_date,
    MIN(event_date) AS first_firebase_event_date,
    COUNT(DISTINCT event_date) AS total_app_active_days,
    COUNT(*) AS total_app_events
  FROM {{ source('raw_data', 'firebase_events') }}
  WHERE user_id IS NOT NULL
  GROUP BY 1
),

braze_users AS (
  SELECT
    external_user_id AS braze_user_id,
    MAX(time) AS last_email_event_time,
    COUNT(DISTINCT CASE WHEN event_type = 'open' THEN send_id END) AS total_email_opens,
    COUNT(DISTINCT CASE WHEN event_type = 'click' THEN send_id END) AS total_email_clicks,
    COUNT(DISTINCT send_id) AS total_emails_received
  FROM {{ source('raw_data', 'braze_email_events') }}
  WHERE external_user_id IS NOT NULL
  GROUP BY 1
),

zendesk_users AS (
  SELECT
    requester_id AS zendesk_user_id,
    COUNT(*) AS total_support_tickets,
    COUNT(DISTINCT CASE WHEN status IN ('new', 'open', 'pending') THEN id END) AS open_support_tickets,
    AVG(CASE
      WHEN solved_at IS NOT NULL
      THEN TIMESTAMP_DIFF(solved_at, created_at, HOUR)
    END) AS avg_ticket_resolution_hours,
    AVG(CASE
      WHEN satisfaction_rating_score IS NOT NULL
      THEN CASE satisfaction_rating_score WHEN 'good' THEN 100 WHEN 'bad' THEN 0 END
    END) AS satisfaction_score
  FROM {{ source('raw_data', 'zendesk_tickets') }}
  WHERE _fivetran_deleted = FALSE
  GROUP BY 1
),

-- Identity resolution: Map all identifiers to a single customer_id
identity_graph AS (
  SELECT DISTINCT
    -- Generate unified customer_id (use email as primary key)
    {{ dbt_utils.surrogate_key(['LOWER(TRIM(email))']) }} AS customer_id,
    LOWER(TRIM(email)) AS email,

    -- Salesforce IDs
    MAX(sf_accounts.salesforce_account_id) AS salesforce_account_id,
    MAX(sf_contacts.salesforce_contact_id) AS salesforce_contact_id,
    MAX(sf_leads.salesforce_lead_id) AS salesforce_lead_id,

    -- Other system IDs
    MAX(shopify.shopify_customer_id) AS shopify_customer_id,
    MAX(ga360.ga360_user_id) AS ga360_user_id,
    MAX(firebase.firebase_user_id) AS firebase_user_id,
    MAX(braze.braze_user_id) AS braze_user_id,
    MAX(zendesk.zendesk_user_id) AS zendesk_user_id

  FROM (
    -- All unique emails from all sources
    SELECT DISTINCT LOWER(TRIM(email)) AS email FROM salesforce_contacts WHERE email IS NOT NULL
    UNION DISTINCT
    SELECT DISTINCT LOWER(TRIM(email)) FROM salesforce_leads WHERE email IS NOT NULL
    UNION DISTINCT
    SELECT DISTINCT LOWER(TRIM(email)) FROM shopify_customers WHERE email IS NOT NULL
  ) all_emails

  LEFT JOIN salesforce_contacts sf_contacts ON LOWER(TRIM(sf_contacts.email)) = all_emails.email
  LEFT JOIN salesforce_accounts sf_accounts ON sf_contacts.salesforce_account_id = sf_accounts.salesforce_account_id
  LEFT JOIN salesforce_leads sf_leads ON LOWER(TRIM(sf_leads.email)) = all_emails.email
  LEFT JOIN shopify_customers shopify ON LOWER(TRIM(shopify.email)) = all_emails.email
  LEFT JOIN ga360_users ga360 ON CAST(ga360.ga360_user_id AS STRING) = all_emails.email
  LEFT JOIN firebase_users firebase ON firebase.firebase_user_id = all_emails.email
  LEFT JOIN braze_users braze ON braze.braze_user_id = all_emails.email
  LEFT JOIN zendesk_users zendesk ON CAST(zendesk.zendesk_user_id AS STRING) = all_emails.email

  GROUP BY customer_id, email
),

-- Unified customer data
unified_customers AS (
  SELECT
    id.customer_id,
    id.email,

    -- Identifiers
    id.salesforce_account_id,
    id.salesforce_contact_id,
    id.salesforce_lead_id,
    id.shopify_customer_id,
    id.ga360_user_id,
    id.firebase_user_id,
    id.braze_user_id,
    id.zendesk_user_id,

    -- Demographics (prefer Salesforce, fall back to Shopify)
    COALESCE(sf_contacts.first_name, sf_leads.first_name, shopify.first_name) AS first_name,
    COALESCE(sf_contacts.last_name, sf_leads.last_name, shopify.last_name) AS last_name,
    COALESCE(
      CONCAT(sf_contacts.first_name, ' ', sf_contacts.last_name),
      CONCAT(sf_leads.first_name, ' ', sf_leads.last_name),
      CONCAT(shopify.first_name, ' ', shopify.last_name)
    ) AS full_name,
    COALESCE(sf_contacts.phone, sf_leads.phone) AS phone,
    COALESCE(sf_accounts.company, sf_leads.company) AS company,
    COALESCE(sf_contacts.title, sf_leads.title) AS title,
    sf_accounts.industry,

    -- Geographic
    sf_accounts.country,
    sf_accounts.state,
    sf_accounts.city,
    sf_accounts.postal_code,

    -- Firmographics
    sf_accounts.company_size,
    sf_accounts.annual_revenue,
    sf_accounts.customer_tier,

    -- Status and lifecycle
    CASE
      WHEN shopify.shopify_customer_id IS NOT NULL THEN TRUE
      WHEN sf_accounts.salesforce_account_id IS NOT NULL THEN TRUE
      ELSE FALSE
    END AS is_customer,

    CASE
      WHEN sf_leads.lead_status IN ('new', 'contacted') AND NOT sf_leads.is_converted THEN 'lead'
      WHEN sf_leads.lead_status = 'qualified' AND NOT sf_leads.is_converted THEN 'mql'
      WHEN sf_accounts.salesforce_account_id IS NOT NULL THEN 'customer'
      ELSE 'prospect'
    END AS lifecycle_stage,

    'active' AS customer_status,  -- Simplified for now, will enhance with churn logic

    -- Financial metrics from Shopify
    COALESCE(shopify.shopify_lifetime_revenue, 0) AS total_revenue,
    COALESCE(shopify.shopify_order_count, 0) AS total_orders,
    SAFE_DIVIDE(shopify.shopify_lifetime_revenue, NULLIF(shopify.shopify_order_count, 0)) AS average_order_value,
    shopify.shopify_lifetime_revenue AS lifetime_value,
    NULL AS predicted_clv,  -- Will be populated by ML model

    -- Engagement scores
    NULL AS lead_score,  -- Will be populated by ML model
    NULL AS engagement_score,  -- Will be calculated in separate model

    -- Email engagement (from Braze)
    SAFE_DIVIDE(braze.total_email_opens, NULLIF(braze.total_emails_received, 0)) AS email_engagement_score,

    -- Web engagement (from GA360)
    CAST(ga360.total_pageviews AS FLOAT64) AS web_engagement_score,  -- Simplified

    -- Product engagement (from Firebase)
    CAST(firebase.total_app_events AS FLOAT64) AS product_engagement_score,  -- Simplified

    -- Risk indicators
    NULL AS churn_risk_score,  -- Will be populated by ML model
    NULL AS churn_risk_category,

    -- Acquisition
    COALESCE(
      DATE(sf_accounts.salesforce_created_date),
      DATE(shopify.shopify_created_date)
    ) AS acquisition_date,
    sf_leads.lead_source AS acquisition_source,
    NULL AS acquisition_medium,
    NULL AS acquisition_campaign,
    NULL AS first_touch_channel,
    NULL AS last_touch_channel,

    -- Activity timestamps
    LEAST(
      DATE(sf_contacts.created_date),
      DATE(sf_leads.lead_created_date),
      DATE(shopify.shopify_created_date),
      ga360.first_ga360_visit,
      firebase.first_firebase_event_date
    ) AS first_seen_date,

    GREATEST(
      DATE(sf_contacts.last_modified_date),
      DATE(shopify.shopify_updated_date),
      ga360.last_ga360_visit,
      firebase.last_firebase_event_date,
      DATE(braze.last_email_event_time)
    ) AS last_seen_date,

    NULL AS last_purchase_date,  -- Will join with transactions
    DATE(braze.last_email_event_time) AS last_email_open_date,
    ga360.last_ga360_visit AS last_web_visit_date,
    NULL AS last_support_ticket_date,  -- Will join with zendesk

    -- Preferences
    TRUE AS email_opt_in,  -- Assume opted in if in Braze
    FALSE AS sms_opt_in,
    'email' AS preferred_communication_channel,

    -- Support metrics
    COALESCE(zendesk.total_support_tickets, 0) AS total_support_tickets,
    COALESCE(zendesk.open_support_tickets, 0) AS open_support_tickets,
    zendesk.avg_ticket_resolution_hours,
    zendesk.satisfaction_score,

    -- Metadata
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at,
    CURRENT_TIMESTAMP() AS dbt_updated_at,

    -- Data quality flags
    REGEXP_CONTAINS(id.email, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') AS email_is_valid,
    sf_contacts.phone IS NOT NULL AS phone_is_valid,
    (sf_accounts.country IS NOT NULL AND sf_accounts.city IS NOT NULL) AS address_is_complete,

    -- Profile completeness (count non-null important fields)
    SAFE_DIVIDE(
      CAST((
        CASE WHEN id.email IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN sf_contacts.first_name IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN sf_contacts.last_name IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN sf_contacts.phone IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN sf_accounts.company IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN sf_contacts.title IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN sf_accounts.industry IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN sf_accounts.country IS NOT NULL THEN 1 ELSE 0 END
      ) AS FLOAT64),
      8.0
    ) * 100 AS profile_completeness_score

  FROM identity_graph id
  LEFT JOIN salesforce_contacts sf_contacts ON id.salesforce_contact_id = sf_contacts.salesforce_contact_id
  LEFT JOIN salesforce_accounts sf_accounts ON id.salesforce_account_id = sf_accounts.salesforce_account_id
  LEFT JOIN salesforce_leads sf_leads ON id.salesforce_lead_id = sf_leads.salesforce_lead_id
  LEFT JOIN shopify_customers shopify ON id.shopify_customer_id = shopify.shopify_customer_id
  LEFT JOIN ga360_users ga360 ON id.ga360_user_id = ga360.ga360_user_id
  LEFT JOIN firebase_users firebase ON id.firebase_user_id = firebase.firebase_user_id
  LEFT JOIN braze_users braze ON id.braze_user_id = braze.braze_user_id
  LEFT JOIN zendesk_users zendesk ON id.zendesk_user_id = zendesk.zendesk_user_id
)

SELECT * FROM unified_customers
