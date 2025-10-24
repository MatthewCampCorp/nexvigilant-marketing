# Architecture Overview: Autonomous Marketing Engine

## Executive Summary
This document provides a comprehensive technical architecture for the NexVigilant Autonomous Marketing Engine, a cloud-native, AI-powered marketing automation system built on Google Cloud Platform. The architecture implements a modern data stack with a central data warehouse, advanced ML/AI capabilities, and automated decision-making systems.

## Architectural Principles

### 1. Data-Centric Design
- **Single Source of Truth**: All customer data flows into and is unified within BigQuery
- **Data as a Product**: Treated as a strategic asset with clear ownership and quality standards
- **Analytics Engineering**: dbt-style transformations create clean, modeled data layers

### 2. Cloud-Native & Serverless
- Leverage managed services to minimize operational overhead
- Auto-scaling infrastructure that adapts to demand
- Pay-per-use pricing model for cost efficiency

### 3. AI-First Approach
- AI capabilities integrated at every layer, not bolted on
- Continuous learning loops that improve performance over time
- Human-in-the-loop for critical decisions, autonomous for optimization

### 4. API-First Integration
- All components expose and consume APIs
- Platform-agnostic integration patterns
- Reverse ETL to operationalize insights

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  CRM        │  Website   │  Mobile    │  Social    │  Ad        │  Offline  │
│ (Salesforce)│  (GA360)   │   App      │  Media     │ Platforms  │  Events   │
└──────┬──────┴──────┬─────┴──────┬─────┴──────┬─────┴──────┬─────┴──────┬────┘
       │             │            │            │            │            │
       └─────────────┴────────────┴────────────┴────────────┴────────────┘
                                    │
                        ┌───────────▼───────────┐
                        │  INGESTION LAYER      │
                        │  ETL/ELT Pipelines    │
                        │  - Fivetran           │
                        │  - Datastream         │
                        │  - Pub/Sub (Streaming)│
                        │  - Cloud Functions    │
                        └───────────┬───────────┘
                                    │
              ┌─────────────────────▼─────────────────────┐
              │     DATA WAREHOUSE LAYER (BigQuery)        │
              ├────────────────────────────────────────────┤
              │  Raw Layer   │  Staging  │  Marts Layer    │
              │  (Ingested)  │  (Clean)  │  (Business)     │
              ├────────────────────────────────────────────┤
              │  • Unified Customer Profiles (360° View)   │
              │  • Event Stream (Behavioral Data)          │
              │  • Campaign Performance                    │
              │  • Transaction History                     │
              └───────────┬───────────────┬────────────────┘
                          │               │
                ┌─────────▼───────┐      │
                │  ANALYTICS LAYER│      │
                │  - Looker/BI    │      │
                │  - SQL Analysis │      │
                │  - dbt Models   │      │
                └─────────────────┘      │
                                         │
                          ┌──────────────▼──────────────┐
                          │   AI/ML LAYER (Vertex AI)   │
                          ├─────────────────────────────┤
                          │  PREDICTIVE MODELS          │
                          │  - Lead Scoring             │
                          │  - Churn Prediction         │
                          │  - CLV Forecasting          │
                          │  - Propensity Models        │
                          ├─────────────────────────────┤
                          │  GENERATIVE AI (Gemini)     │
                          │  - Content Generation       │
                          │  - Image Creation (Imagen)  │
                          │  - Personalization          │
                          ├─────────────────────────────┤
                          │  DECISION ENGINES           │
                          │  - Real-Time Bidding        │
                          │  - Journey Orchestration    │
                          │  - A/B Testing Optimization │
                          └──────────────┬──────────────┘
                                         │
                          ┌──────────────▼──────────────┐
                          │  REVERSE ETL LAYER          │
                          │  (Hightouch/Census)         │
                          │  - Sync Insights to Apps    │
                          │  - Audience Activation      │
                          └──────────────┬──────────────┘
                                         │
                ┌────────────────────────┴────────────────────────┐
                │                                                 │
      ┌─────────▼─────────┐                           ┌──────────▼──────────┐
      │  ACTIVATION LAYER  │                           │  ENGAGEMENT LAYER   │
      ├────────────────────┤                           ├─────────────────────┤
      │ • CRM (Salesforce) │                           │ • Email (Braze)     │
      │ • Marketing Auto   │                           │ • Push/SMS          │
      │ • Google Ads       │                           │ • Chatbots          │
      │ • DV360/SA360      │                           │   (Dialogflow)      │
      │ • Social Ads       │                           │ • Web Personalize   │
      └────────────────────┘                           └─────────────────────┘
                │                                                 │
                └─────────────────────┬───────────────────────────┘
                                      │
                          ┌───────────▼────────────┐
                          │   CUSTOMER TOUCHPOINTS │
                          │   - Website            │
                          │   - Mobile App         │
                          │   - Email              │
                          │   - Ads                │
                          │   - Chat               │
                          └────────────────────────┘
```

## Layer-by-Layer Architecture

### 1. Data Source Layer
**Purpose**: Capture all customer interactions and business data

**Components**:
- **CRM Systems**: Salesforce, HubSpot (contact data, deals, activities)
- **Web Analytics**: Google Analytics 360 (behavioral data, sessions, conversions)
- **Mobile Apps**: Firebase, Amplitude (app events, user properties)
- **Social Media**: Facebook, LinkedIn, Twitter APIs (engagement, ad performance)
- **Ad Platforms**: Google Ads, DV360, Facebook Ads (campaign performance, spend)
- **Offline Sources**: Point-of-sale, event registrations, call center logs

**Technical Considerations**:
- API rate limits and pagination
- Data freshness requirements (real-time vs. batch)
- Schema evolution and backwards compatibility

### 2. Ingestion Layer
**Purpose**: Reliably move data from sources into the data warehouse

**Architecture Pattern**: Lambda (Batch + Streaming)

#### Batch Ingestion
- **Tools**: Fivetran, Stitch, Cloud Data Transfer Service
- **Frequency**: Hourly or daily syncs
- **Use Cases**: Historical CRM data, offline sources, daily reports
- **Implementation**:
  ```
  Source API → Fivetran → BigQuery Raw Tables
  ```

#### Streaming Ingestion
- **Tools**: Google Pub/Sub, Datastream, Cloud Functions
- **Latency**: Seconds to minutes
- **Use Cases**: Website events, mobile app events, real-time campaign data
- **Implementation**:
  ```
  Event → Pub/Sub Topic → Dataflow/Cloud Function → BigQuery Streaming Insert
  ```

#### Change Data Capture (CDC)
- **Tool**: Datastream
- **Purpose**: Capture database changes in real-time
- **Use Cases**: Salesforce updates, database replicas
- **Implementation**:
  ```
  Source DB → Datastream (CDC) → BigQuery
  ```

**Key Design Decisions**:
- **Schema-on-Read**: Store raw JSON in BigQuery, parse during transformation
- **Idempotency**: Ensure duplicate events don't corrupt data
- **Error Handling**: Dead-letter queues for failed records
- **Monitoring**: Data quality checks, pipeline lag alerts

### 3. Data Warehouse Layer (BigQuery)
**Purpose**: Central repository and single source of truth for all customer data

#### Data Model Architecture: Medallion Architecture

##### Bronze Layer (Raw)
- Exact copy of source data, minimal transformation
- Preserves full history and allows reprocessing
- Schema: `raw_<source>_<table>`
- Example: `raw_salesforce_contacts`, `raw_ga360_events`

##### Silver Layer (Staging/Clean)
- Cleaned, deduplicated, typed data
- Standardized naming conventions
- Business logic applied
- Schema: `staging_<domain>_<entity>`
- Example: `staging_customers_profiles`, `staging_web_sessions`

##### Gold Layer (Business/Marts)
- Aggregated, enriched, ready-for-consumption tables
- Optimized for specific use cases
- Joins across domains
- Schema: `marts_<business_function>_<purpose>`
- Example: `marts_marketing_customer_360`, `marts_sales_lead_scores`

#### Key Tables

**Unified Customer Profile** (`marts_marketing_customer_360`)
```sql
customer_id (primary key)
email
first_name, last_name
acquisition_date
acquisition_source
total_purchases
total_revenue
last_purchase_date
predicted_clv
churn_risk_score
lead_score
preferred_channel
lifecycle_stage
customer_segment
```

**Event Stream** (`staging_events_all`)
```sql
event_id (primary key)
customer_id (foreign key)
event_timestamp
event_type (page_view, email_open, purchase, etc.)
event_properties (JSON)
session_id
device_type
source, medium, campaign
```

**Campaign Performance** (`marts_marketing_campaign_performance`)
```sql
campaign_id (primary key)
campaign_name
channel
start_date, end_date
impressions, clicks, conversions
spend
revenue
roas
attributed_touches
```

#### BigQuery Optimization Strategies
- **Partitioning**: By date for time-series data
- **Clustering**: By customer_id, campaign_id for faster lookups
- **Materialized Views**: Pre-compute expensive aggregations
- **BI Engine**: In-memory acceleration for dashboards

### 4. Analytics Layer
**Purpose**: Enable business intelligence and ad-hoc analysis

**Tools**:
- **Looker**: Primary BI platform, semantic layer, embedded analytics
- **Data Studio**: Self-service dashboards
- **dbt (data build tool)**: Transform raw data into business models

**dbt Workflow**:
```
Raw BigQuery Tables → dbt Models (SQL) → Staging → Marts → BI Tools
```

**Key dbt Capabilities**:
- Version-controlled transformations (SQL as code)
- Automated testing (schema tests, custom tests)
- Documentation generation
- Incremental model builds for efficiency

### 5. AI/ML Layer (Vertex AI)
**Purpose**: Build, train, and deploy machine learning models

#### Predictive Analytics Models

**Lead Scoring Model**
- **Type**: Binary Classification (Convert / No Convert)
- **Algorithm**: XGBoost, Neural Network
- **Features**: Demographic data, behavioral signals, firmographics
- **Training**: Historical lead data (6-12 months)
- **Output**: Probability score (0-100) for each lead
- **Deployment**: Vertex AI Endpoint, batch prediction to BigQuery
- **Refresh**: Weekly retraining

**Churn Prediction Model**
- **Type**: Binary Classification (Churn / Retain)
- **Algorithm**: Random Forest, Gradient Boosting
- **Features**: Usage patterns, engagement metrics, support tickets, payment history
- **Training**: Historical customer data with churn labels
- **Output**: Churn probability and risk tier (High/Medium/Low)
- **Deployment**: Batch prediction, daily scoring
- **Trigger**: Scores > 70% trigger retention workflows

**CLV Forecasting Model**
- **Type**: Regression
- **Algorithm**: Linear Regression, XGBoost
- **Features**: Purchase history, frequency, recency, AOV, segment
- **Output**: Predicted lifetime value ($)
- **Use Case**: Budget allocation, VIP identification

#### Generative AI (Gemini)

**Content Generation Workflows**
- **Email Subject Lines**: Generate 10 variations, A/B test top 3
- **Ad Copy**: Create copy tailored to audience segment
- **Product Descriptions**: Scale content for large catalogs
- **Social Posts**: Draft weekly content calendar
- **Blog Outlines**: Generate topic ideas and outlines

**Implementation Pattern**:
```python
from vertexai.preview.generative_models import GenerativeModel

model = GenerativeModel("gemini-1.5-pro")
prompt = f"Generate 5 email subject lines for {product} targeting {segment}"
response = model.generate_content(prompt)
```

**Image Generation (Imagen)**
- Product lifestyle images
- Ad creative variations
- Social media visuals

#### Decision Engines

**Real-Time Bidding Engine**
- **Input**: Ad auction context (user profile, time, device, inventory)
- **Process**: Predict conversion probability, calculate optimal bid
- **Output**: Bid amount (milliseconds)
- **Technology**: Vertex AI Prediction with low-latency endpoints

**Journey Orchestration Engine**
- **Input**: Customer state (profile, behavior, current journey stage)
- **Process**: Predict next best action and channel
- **Output**: Action recommendation (email, SMS, ad, wait)
- **Technology**: Reinforcement learning model, custom decision logic

### 6. Reverse ETL Layer
**Purpose**: Sync enriched data and AI outputs from BigQuery back to operational tools

**Architecture**:
```
BigQuery (Gold Layer) → Reverse ETL (Hightouch/Census) → Destination Tools
```

**Key Syncs**:

**Salesforce**
- Sync: Lead scores, churn risk, predicted CLV
- Frequency: Every 15 minutes (real-time)
- Mapping: BigQuery `customer_id` → Salesforce `Contact ID`

**Google Ads**
- Sync: High-value customer audiences, lookalike seed lists
- Frequency: Daily
- Use Case: Retargeting, Customer Match campaigns

**Braze (Email/Push)**
- Sync: Behavioral segments, triggered campaign audiences
- Frequency: Real-time (event-triggered)
- Use Case: Personalized journey orchestration

**HubSpot**
- Sync: Engagement scores, lifecycle stage updates
- Frequency: Hourly
- Use Case: Marketing automation workflows

**Tools Comparison**:
| Feature | Hightouch | Census | Segment |
|---------|-----------|--------|---------|
| BigQuery Native | Yes | Yes | Yes |
| Visual Mapper | Yes | Yes | Limited |
| dbt Integration | Yes | Yes | No |
| Pricing | Per-row | Per-row | Per-event |
| Best For | Marketing | Data Teams | Real-time |

### 7. Activation Layer
**Purpose**: Execute marketing campaigns across paid and owned channels

**Google Marketing Platform**
- **Display & Video 360**: Programmatic display and video ads
- **Search Ads 360**: Cross-engine search management
- **Campaign Manager 360**: Ad serving and trafficking
- **Ads Data Hub**: Privacy-safe data clean room

**Third-Party Platforms**
- **Salesforce Marketing Cloud**: Email, mobile, social, advertising
- **Adobe Experience Cloud**: Personalization, content management
- **HubSpot**: All-in-one marketing, sales, service

**Integration Pattern**:
```
Reverse ETL → Platform API → Audience/Campaign Creation → Activation
```

### 8. Engagement Layer
**Purpose**: Direct customer communication and interaction

**Email & Mobile** (Braze, Salesforce)
- Personalized email campaigns
- Push notifications
- SMS messaging
- In-app messages

**Conversational AI** (Dialogflow CX)
- Website chatbots
- Voice assistants
- Lead qualification
- 24/7 support

**Web Personalization**
- Dynamic content blocks
- Personalized CTAs
- Product recommendations
- Exit-intent offers

## Data Flow: End-to-End Example

### Scenario: High-Intent Lead Scoring and Automated Follow-Up

1. **Event Capture**: User downloads whitepaper on website
   ```
   Website → GA360 → Pub/Sub → BigQuery (raw_ga360_events)
   ```

2. **Data Unification**: Event joins to customer profile
   ```
   dbt transformation → staging_web_sessions → marts_customer_360
   ```

3. **AI Scoring**: Lead score recalculated
   ```
   Vertex AI Batch Prediction → BigQuery (marts_sales_lead_scores)
   Score: 85/100 (High Intent)
   ```

4. **Reverse ETL**: Score synced to CRM
   ```
   Hightouch → Salesforce Contact Record (Lead Score field updated)
   ```

5. **Automation Trigger**: High score triggers workflow
   ```
   Salesforce Flow: If Lead Score > 80 → Create Task for Sales Rep
   ```

6. **Sales Engagement**: Rep receives alert, initiates outreach
   ```
   Salesforce Task → Email/Call → Opportunity Created
   ```

7. **Feedback Loop**: Outcome feeds back to model
   ```
   Salesforce → Fivetran → BigQuery → Model Retraining Data
   ```

## Security & Compliance Architecture

### Data Governance
- **Access Control**: IAM roles and BigQuery column-level security
- **Data Encryption**: At-rest and in-transit (TLS)
- **Audit Logging**: Cloud Audit Logs for all data access
- **Data Lineage**: Track data from source to activation

### Privacy Compliance
- **GDPR**: Right to access, deletion, portability
- **CCPA**: Opt-out mechanisms, data transparency
- **Cookie Consent**: Consent management platform integration
- **PII Handling**: Tokenization, hashing, secure storage

### Ethical AI Framework
- **Bias Testing**: Regular model audits for demographic fairness
- **Explainability**: SHAP values for model interpretability
- **Human Oversight**: Critical decisions require human approval
- **Transparency**: Clear disclosure of AI-generated content

## Scalability & Performance

### Handling Growth
- **BigQuery**: Scales to petabytes, auto-scaling compute
- **Vertex AI**: Managed infrastructure, auto-scaling endpoints
- **Pub/Sub**: Handles millions of events per second
- **Cloud Functions**: Auto-scales based on request volume

### Performance Optimization
- **Caching**: BI Engine for sub-second dashboard queries
- **Batch Processing**: Scheduled off-peak for heavy workloads
- **Streaming**: Real-time for time-sensitive use cases
- **Indexing**: Clustering and partitioning for query performance

## Monitoring & Observability

### Key Metrics
- **Data Pipeline Health**: Lag, throughput, error rate
- **Model Performance**: Accuracy drift, prediction latency
- **System Performance**: API response times, uptime
- **Business KPIs**: Conversion rate, ROAS, CLV

### Tools
- **Cloud Monitoring**: Infrastructure and application metrics
- **Cloud Logging**: Centralized log aggregation
- **Vertex AI Model Monitoring**: Drift detection, performance alerts
- **Custom Dashboards**: Looker/Data Studio for business metrics

## Cost Management

### Cost Optimization Strategies
- **BigQuery**: Flat-rate pricing for predictable costs, query optimization
- **Vertex AI**: Batch prediction for non-real-time use cases
- **Storage**: Lifecycle policies to move old data to cheaper tiers
- **Reserved Resources**: Committed use discounts for stable workloads

### Budget Alerts
- Set billing alerts at 50%, 75%, 90% of monthly budget
- Per-project budgets to isolate cost drivers
- Regular cost reviews and optimization sprints

## Disaster Recovery & Business Continuity

### Backup Strategy
- **BigQuery**: Automatic 7-day time travel, manual snapshots
- **Vertex AI**: Model versioning, artifact storage in Cloud Storage
- **Configuration**: Infrastructure-as-Code (Terraform) in version control

### Failover
- **Multi-Region**: Deploy critical components across regions
- **Health Checks**: Automated monitoring and alerting
- **Runbooks**: Documented incident response procedures

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Owner**: Data & AI Engineering Team
**Review Cycle**: Quarterly
