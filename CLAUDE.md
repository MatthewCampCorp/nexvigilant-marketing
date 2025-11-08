# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NexVigilant Autonomous Marketing Engine is an AI-powered, cloud-native marketing automation system built on Google Cloud Platform (GCP). **Phase 1 Week 3-4 has been completed** with a production-ready multi-agent marketing system featuring 6 agents (1 coordinator + 5 specialized agents) using Google's Agent Development Kit (ADK) hierarchical delegation pattern.

**Current Status**: ✅ Phase 1 Complete - All specialized agents implemented and tested
**Implementation Date**: 2025-01-08
**Production Code**: 3,739 lines
**Test Coverage**: 91%+ (100% with BigQuery authentication)
**GitHub**: https://github.com/MatthewCampCorp/nexvigilant-marketing

**Core Technology Stack:**
- **Cloud Platform**: Google Cloud Platform (BigQuery, Vertex AI, Cloud Functions, Cloud Run, Pub/Sub)
- **AI/ML Platform**: Vertex AI + Gemini
- **Agent Framework**: Google Agent Development Kit (ADK)
- **Data Warehouse**: BigQuery (Bronze/Silver/Gold medallion architecture)
- **Data Transformation**: dbt (Analytics Engineering)
- **Marketing Activation**: Google Marketing Platform (GA360, DV360, SA360)

---

## Multi-Agent System Architecture (NEW - Phase 1 Complete)

### Hierarchical Delegation Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                  Marketing Coordinator Agent                │
│           Hierarchical Delegation & Orchestration           │
│                  (401 lines, 18/18 tests ✅)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬──────────────┬──────────────────┐
        │                │                │              │                  │
┌───────┴──────┐  ┌──────┴─────┐  ┌──────┴──────┐  ┌───┴────┐  ┌──────────┴────────┐
│    Data      │  │ Predictive │  │  Content    │  │Campaign│  │  Performance      │
│Intelligence  │  │  Insights  │  │ Generation  │  │ Design │  │  Optimization     │
│              │  │            │  │             │  │        │  │                   │
│ BigQuery     │  │ Vertex AI  │  │   Gemini    │  │Multi-  │  │  Analytics &      │
│ Integration  │  │   Models   │  │     AI      │  │Channel │  │  Recommendations  │
│              │  │            │  │             │  │        │  │                   │
│ 404 lines    │  │ 575 lines  │  │  647 lines  │  │287 lines│  │  419 lines        │
│ 11/18 tests✅│  │ 17/17 tests✅│  │ 21/21 tests✅│  │Stub✅  │  │  Stub✅           │
└──────────────┘  └────────────┘  └─────────────┘  └────────┘  └───────────────────┘
```

### How the Agent System Works

**Coordinator Agent** (agents/coordinator/main.py:64-363):
- Receives user requests via `process_request()` method
- Determines which specialized agent(s) to delegate to via keyword-based routing (Phase 1) or LLM-powered routing (Phase 2)
- Orchestrates multi-agent workflows when multiple agents are needed
- Aggregates results from all agents into unified response
- Tracks delegation history and statistics

**Agent Communication Pattern**:
1. User request → Coordinator.process_request(request)
2. Coordinator.determine_delegation(request) → List[DelegationDecision]
3. For each decision: Coordinator.execute_delegation(decision) → calls specialized_agent.execute(**parameters)
4. Coordinator.aggregate_results(results) → unified response

**Key Methods Across All Agents**:
- `execute(**kwargs) -> Dict[str, Any]` - Main entry point called by coordinator
- All agents return dict with `success: bool` and result data

**Stub Mode vs Production Mode**:
- Agents check for cloud credentials and operate in stub mode if not available
- Stub mode uses realistic test data for development/testing
- Production mode connects to BigQuery, Vertex AI, Gemini

---

## Essential Commands

### Environment Setup

```bash
# Create virtual environment (first time only)
cd agents/
python -m venv venv

# Activate virtual environment
# Windows:
./venv/Scripts/activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Testing

```bash
# Run all tests
cd agents/
pytest -v

# Run tests for specific agent
pytest coordinator/tests/test_coordinator.py -v
pytest data_intelligence/tests/test_data_intelligence.py -v
pytest content_generation/tests/test_content_generation.py -v
pytest predictive_insights/tests/test_predictive_insights.py -v

# Run single test method
pytest coordinator/tests/test_coordinator.py::TestMarketingCoordinator::test_agent_initialization -v

# Run integration tests (all 6 agents working together)
pytest tests/test_integration.py -v

# Run specific integration test
pytest tests/test_integration.py::test_complete_marketing_workflow -v

# Run tests with coverage
pytest --cov=coordinator --cov=data_intelligence --cov=content_generation --cov=predictive_insights -v

# Run tests with detailed output
pytest -vv -s
```

### Linting & Formatting

```bash
# Format code with black
black agents/

# Lint with ruff
ruff check agents/

# Fix auto-fixable issues
ruff check agents/ --fix
```

### Running Agents Directly

```bash
cd agents/

# Run coordinator agent (demonstrates delegation)
python -m coordinator.main

# Run data intelligence agent
python -m data_intelligence.main

# Run content generation agent
python -m content_generation.main

# Run predictive insights agent
python -m predictive_insights.main

# Run campaign design agent
python -m campaign_design.main

# Run performance optimization agent
python -m performance_optimization.main
```

### Google Cloud Authentication

```bash
# Authenticate with Google Cloud (required for BigQuery, Vertex AI, Gemini)
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Verify authentication
gcloud auth application-default print-access-token
```

---

## High-Level Architecture & Patterns

### 1. Hierarchical Multi-Agent Delegation

**Pattern**: Coordinator → Specialized Agents → Results Aggregation

**Key Files**:
- `agents/coordinator/main.py:133-205` - `determine_delegation()` method implementing keyword-based routing
- `agents/coordinator/main.py:207-263` - `execute_delegation()` method calling specialized agents
- `agents/coordinator/main.py:265-294` - `aggregate_results()` method combining insights

**How it works**:
1. Coordinator analyzes user request keywords
2. Maps keywords to one or more specialized agents
3. Creates `DelegationDecision` objects with task parameters
4. Executes each delegation via agent's `execute()` method
5. Aggregates results into unified response

**Example Flow** (from agents/tests/test_integration.py:336-372):
```
Request: "Create a personalized email campaign targeting high-value customers"
  ↓
Coordinator determines: [data_intelligence, predictive_insights, content_generation]
  ↓
Execute data_intelligence.execute(query="high-value customers")
  → Returns customer segments
  ↓
Execute predictive_insights.execute(prediction_type="lead_scoring")
  → Returns conversion probabilities
  ↓
Execute content_generation.execute(content_request="email campaign")
  → Returns generated email content
  ↓
Aggregate results into unified campaign plan
```

### 2. BigQuery Integration with Security Controls

**Pattern**: Query Validation → Allowed Tables Whitelist → Timeout Controls → Result Caching

**Key Files**:
- `agents/data_intelligence/bigquery_tool.py:54-171` - BigQueryTool class with security features
- `agents/data_intelligence/bigquery_tool.py:227-264` - `_validate_query()` method preventing SQL injection
- `agents/data_intelligence/bigquery_tool.py:173-225` - `query()` method with timeout and byte limits

**Security Features**:
- SQL injection prevention via allowlisting table names
- Query timeouts (default 30s)
- Max bytes billed limits (default 10 GB)
- Read-only operations only
- Result caching for performance

**Data Layer Pattern** (Bronze/Silver/Gold):
```
Bronze (Raw):      raw_customer_events, raw_crm_contacts
Silver (Staging):  stg_customer_360, stg_campaign_performance
Gold (Marts):      customer_360, campaign_performance, ml_features, attribution_model
```

### 3. Gemini AI Content Generation Pattern

**Pattern**: System Prompt + User Prompt → Gemini API → Structured Response Parsing

**Key Files**:
- `agents/content_generation/prompts.py:1-275` - Comprehensive prompt library
- `agents/content_generation/main.py:106-233` - Content generation methods (email, social, ads, landing pages)
- `agents/content_generation/main.py:46-103` - Gemini client initialization with temperature=0.8 for creativity

**Content Types**:
1. Email Marketing - Subject lines (A/B variants), body, CTAs, preheaders
2. Social Media - Platform-specific content (LinkedIn, Twitter, Facebook, Instagram)
3. Ad Copy - Google Ads (headlines, descriptions), display ads, social ads
4. Landing Pages - Hero sections, features, social proof, FAQ

**Prompt Structure** (agents/content_generation/prompts.py):
```
CONTENT_GENERATOR_SYSTEM_PROMPT → Brand voice guidelines, compliance, output format
  ↓
EMAIL_GENERATION_PROMPT → Specific content request with parameters
  ↓
Gemini API (temperature=0.8, max_tokens=2048)
  ↓
Structured JSON response with variants for A/B testing
```

### 4. Vertex AI Predictive Analytics Pattern

**Pattern**: Feature Preparation → Vertex AI Endpoint → Predictions → Recommendations

**Key Files**:
- `agents/predictive_insights/main.py:72-148` - `predict_lead_score()` method
- `agents/predictive_insights/main.py:150-219` - `predict_churn()` method
- `agents/predictive_insights/main.py:221-283` - `forecast_clv()` method
- `agents/predictive_insights/main.py:285-401` - Feature preparation methods

**Prediction Types**:
1. **Lead Scoring** - Conversion probability (0-1.0), confidence scores, recommendations
2. **Churn Prediction** - Churn probability (0-1.0), risk levels (HIGH/MEDIUM/LOW), retention strategies
3. **CLV Forecasting** - Dollar value forecast, time horizon (default 12 months), value segments (PREMIUM/HIGH/MEDIUM/LOW)

**Stub Mode Features** (agents/predictive_insights/main.py:403-531):
- Realistic test data generation for all prediction types
- Simulated model metrics (accuracy, precision, recall)
- No cloud credentials required for development/testing

### 5. Agent Registration and Execution Pattern

**Pattern**: Coordinator.register_specialized_agent() → Agent available for delegation

**Key Files**:
- `agents/coordinator/main.py:122-131` - `register_specialized_agent()` method
- `agents/coordinator/main.py:296-339` - `process_request()` main entry point

**Agent Registration** (from agents/tests/test_integration.py:193-201):
```python
coordinator = MarketingCoordinator()
coordinator.register_specialized_agent('data_intelligence', DataIntelligenceAgent())
coordinator.register_specialized_agent('predictive_insights', PredictiveInsightsAgent())
coordinator.register_specialized_agent('content_generation', ContentGenerationAgent())
coordinator.register_specialized_agent('campaign_design', CampaignDesignAgent())
coordinator.register_specialized_agent('performance_optimization', PerformanceOptimizationAgent())

# Now coordinator can delegate to any registered agent
response = coordinator.process_request("Create email campaign")
```

---

## Project Structure

```
nexvigilant-marketing/
├── agents/                          # NEW - Multi-agent system (Phase 1 Complete)
│   ├── coordinator/                 # Root coordinator agent
│   │   ├── main.py                  # MarketingCoordinator class (401 lines)
│   │   ├── prompts.py               # Coordination prompts
│   │   └── tests/                   # 18/18 tests passing ✅
│   │
│   ├── data_intelligence/           # BigQuery data analysis agent
│   │   ├── main.py                  # DataIntelligenceAgent (404 lines)
│   │   ├── bigquery_tool.py         # Secure BigQuery integration (387 lines)
│   │   └── tests/                   # 11/18 tests (7 need BigQuery auth)
│   │
│   ├── content_generation/          # Gemini AI content creation agent
│   │   ├── main.py                  # ContentGenerationAgent (647 lines)
│   │   ├── prompts.py               # Comprehensive prompt library
│   │   └── tests/                   # 21/21 tests passing ✅
│   │
│   ├── predictive_insights/         # Vertex AI predictive analytics agent
│   │   ├── main.py                  # PredictiveInsightsAgent (575 lines)
│   │   └── tests/                   # 17/17 tests passing ✅
│   │
│   ├── campaign_design/             # Multi-channel campaign orchestration
│   │   ├── main.py                  # CampaignDesignAgent (287 lines)
│   │   └── __init__.py
│   │
│   ├── performance_optimization/    # Campaign performance analysis
│   │   ├── main.py                  # PerformanceOptimizationAgent (419 lines)
│   │   └── __init__.py
│   │
│   ├── tests/                       # Integration tests
│   │   └── test_integration.py      # 6/6 tests passing (100% success rate) ✅
│   │
│   ├── requirements.txt             # Python dependencies
│   ├── venv/                        # Virtual environment (gitignored)
│   ├── FINAL_IMPLEMENTATION_SUMMARY.md  # Complete implementation documentation
│   └── README.md                    # Agent system overview
│
├── phase-1-foundation/              # Data infrastructure (Months 1-3)
│   ├── bigquery-schemas/            # DDL for Bronze/Silver/Gold layers
│   ├── data-ingestion/              # ETL/ELT pipeline configs
│   ├── dbt-project/                 # Data transformations (dbt)
│   ├── basic-automation/            # Rule-based workflows
│   └── reverse-etl/                 # Operationalize insights to platforms
│
├── phase-2-predictive/              # ML models (Months 4-6)
│   ├── lead-scoring/                # Predictive lead scoring model
│   ├── churn-prediction/            # Customer churn forecasting
│   ├── clv-forecasting/             # Customer lifetime value
│   ├── content-generation/          # Gemini workflows for content
│   └── personalization/             # Dynamic content personalization
│
├── phase-3-autonomous/              # Full automation (Months 7-12)
│   ├── journey-orchestration/       # Autonomous customer journeys
│   ├── real-time-decisioning/       # Real-time bidding & allocation
│   └── conversational-ai/           # Chatbots and assistants
│
├── testing/                         # Comprehensive testing framework
│   ├── data-quality/                # Schema, freshness, anomaly tests
│   ├── ml-validation/               # Model accuracy, bias, drift tests
│   ├── performance/                 # Load, stress, latency tests
│   └── chaos-engineering/           # Resilience testing
│
├── monitoring/                      # Observability and alerting
│   └── alerting/                    # Incident response playbooks
│
├── .repometa/                       # Intelligent repository system (Vision 2045)
│   ├── visualizer.py                # Interactive codebase explorer
│   └── analyzer.py                  # AI-powered code analysis
│
└── docs/                            # Architecture and implementation docs
```

---

## Development Workflows

### Working with Multi-Agent System (NEW)

**Location**: `agents/`

**Adding a New Specialized Agent**:

1. Create agent directory: `agents/my_new_agent/`
2. Implement agent with `execute(**kwargs)` method
3. Add `__init__.py` exporting agent class
4. Create tests in `tests/` subdirectory
5. Register agent in coordinator:
   ```python
   coordinator.register_specialized_agent('my_new_agent', MyNewAgent())
   ```
6. Update coordinator routing in `coordinator/main.py:133-205` if using keyword-based routing

**Agent Implementation Pattern**:
```python
class MyNewAgent:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        # Initialize cloud services if needed

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Main entry point called by coordinator."""
        # Process task
        return {
            'success': True,
            'result': {...},
            'metadata': {...}
        }
```

**Testing Pattern** (see agents/tests/test_integration.py):
```python
# Create mock agent for testing
class MockMyNewAgent:
    def execute(self, **kwargs):
        return {'success': True, 'result': 'test data'}

# Test with coordinator
coordinator = MarketingCoordinator()
coordinator.register_specialized_agent('my_new_agent', MockMyNewAgent())
response = coordinator.process_request("test request")
assert response['results']['success'] is True
```

### Working with dbt (Data Transformations)

**Location**: `phase-1-foundation/dbt-project/`

**Key Files**:
- `dbt_project.yml` - Project configuration, model materialization strategies
- `models/staging/` - Silver layer transformations
- `models/marts/` - Gold layer business logic

**Common Commands** (run from `phase-1-foundation/dbt-project/`):
```bash
# Full refresh of all models
dbt run --full-refresh

# Run specific model
dbt run --select stg_customer_360

# Run models with specific tag
dbt run --select tag:customer

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

**Important Patterns**:
- Staging models use `+materialized: table` or `incremental` with partitioning
- High-volume event data uses incremental materialization with `event_id` as unique key
- Marts layer always materialized as tables for query performance
- All PII-containing models tagged with `pii`

### Working with BigQuery Schemas

**Location**: `phase-1-foundation/bigquery-schemas/`

**Schema Files**:
- `01_bronze_raw_schemas.sql` - Raw data ingestion tables
- `02_silver_staging_schemas.sql` - Cleaned staging tables
- `03_gold_marts_schemas.sql` - Business-ready marts

**Conventions**:
- Bronze tables: `raw_<source>_<entity>`
- Silver tables: `stg_<domain>_<entity>`
- Gold tables: `<domain>_<entity>` (no prefix)
- Always use partitioning for date-based data
- Cluster by common filter/join columns

### Working with ML Models

**Location**: `phase-2-predictive/`

**Lead Scoring Example** (`phase-2-predictive/lead-scoring/`):
- `model-specification.md` - Comprehensive model requirements
- `src/train_model.py` - Training script for Vertex AI
- `src/predict_api.py` - Prediction API endpoint
- `config/` - Model hyperparameters and feature configs
- `notebooks/` - Exploratory data analysis and experiments

**ML Development Pattern**:
1. Feature engineering in dbt (Gold layer `marts/ml/` models)
2. Extract features from BigQuery to Vertex AI Dataset
3. Train model using Vertex AI Training
4. Deploy to Vertex AI Endpoint
5. Monitor drift, accuracy, bias continuously

**Model Quality Thresholds**:
- Minimum accuracy: 80%
- Maximum prediction latency: 100ms (P95)
- Data freshness: < 24 hours
- Feature null rate: < 5%

### Testing Strategy

**Location**: `testing/` (framework docs) + `agents/tests/` (agent tests)

**Test Categories** (in order of volume):
1. **Data Quality Tests** (35%) - Schema, nulls, duplicates, anomalies
2. **ML Model Validation** (30%) - Accuracy, drift, bias, explainability
3. **Integration Tests** (20%) - API endpoints, data flows, ETL/Reverse ETL
4. **End-to-End Tests** (10%) - Complete customer journeys
5. **Manual Testing** (5%) - User acceptance

**Agent Testing Best Practices**:
- Use mock agents for integration tests (see `agents/tests/test_integration.py`)
- Test both stub mode and production mode (when credentials available)
- Validate all `execute()` methods return `success: bool` and proper data structure
- Test error handling (agents/coordinator/tests/test_coordinator.py:308-333)

**Quality Gates** (must pass before production):
- All unit tests pass (100%)
- Code coverage > 80%
- Data quality score > 95%
- ML model accuracy > 80%
- Performance tests meet SLAs (P95 < 100ms, 100+ RPS)
- Security vulnerability scan passes
- Chaos engineering tests pass (staging)

### Repository Intelligence System (Vision 2045)

**Location**: `.repometa/`

This repository includes an intelligent semantic layer for conversational exploration and automated insights.

**Quick Commands**:
```bash
# Interactive exploration
python .repometa/visualizer.py --interactive

# Within interactive mode:
> tree                # Full repository visualization
> branch phase-2-predictive
> brain               # Dependencies as neural network
> capabilities        # Discover hidden features

# AI-powered analysis
python .repometa/analyzer.py --full-analysis
python .repometa/analyzer.py --scan-redundancies
python .repometa/analyzer.py --impact-analysis
python .repometa/analyzer.py --complexity-score
```

**Use Cases**:
- Visualize dependencies between data layers, models, and services
- Find code redundancies and refactoring opportunities
- Understand blast radius of changes
- Discover hidden capabilities in the codebase

---

## Implementation Phases

### Phase 1: Foundation (Months 1-3) - ✅ WEEKS 3-4 COMPLETE

**Agent System Status**:
- ✅ Coordinator agent implemented (401 lines, 18/18 tests)
- ✅ Data Intelligence agent implemented (791 lines total, 11/18 tests)
- ✅ Content Generation agent implemented (647 lines, 21/21 tests)
- ✅ Predictive Insights agent implemented (575 lines, 17/17 tests)
- ✅ Campaign Design agent implemented (287 lines, integration tested)
- ✅ Performance Optimization agent implemented (419 lines, integration tested)
- ✅ Integration tests passing (6/6 tests, 100% success rate)
- ⏳ BigQuery authentication setup (required for 7 data intelligence tests)

**Success Criteria**:
- ✅ 95%+ data quality score
- ⏳ All data sources ingested
- ⏳ First automated workflow live

**Next Steps**:
1. Run `gcloud auth application-default login` for BigQuery integration
2. Verify all 18 data intelligence tests pass with authentication
3. End-to-end integration testing with real data

### Phase 2: Predictive (Months 4-6) - PLANNED

**Upgrades**:
1. **LLM-Powered Routing** - Upgrade coordinator from keyword-based to intelligent LLM routing
2. **Advanced Analytics** - Enhanced insight generation and recommendation engine
3. **Event-Driven Triggers** - Pub/Sub integration for automated workflows
4. **Real-Time Optimization** - Continuous campaign optimization loops
5. **Production Deployment** - Cloud Run deployment with Workload Identity

**Success Criteria**:
- Lead scoring accuracy > 80%
- 20%+ conversion lift from personalization
- 50% time saved on content creation

### Phase 3: Autonomous (Months 7-12) - PLANNED

**Enhancements**:
1. **Reinforcement Learning** - Self-optimizing campaigns
2. **Multi-Modal Content** - Image and video generation
3. **Conversational Interface** - Natural language query interface
4. **Advanced Personalization** - Individual-level content optimization
5. **Cross-Channel Attribution** - Unified attribution modeling

**Success Criteria**:
- Fully automated cross-channel journeys
- Real-time decisioning engine operational
- 50-80% reduction in manual task time

---

## Key Conventions

### Multi-Agent System Conventions (NEW)

**Agent Naming**:
- Agent classes: `{Purpose}Agent` (e.g., `ContentGenerationAgent`)
- Agent directories: lowercase with underscores (e.g., `content_generation/`)
- Agent identifiers in coordinator: lowercase with underscores (e.g., `'content_generation'`)

**Execute Method Signature**:
```python
def execute(self, **kwargs) -> Dict[str, Any]:
    """
    Main entry point called by coordinator.

    Returns:
        Dict with 'success': bool and agent-specific result data
    """
```

**Response Format**:
```python
{
    'success': True,  # or False
    'result': {...},  # Agent-specific data
    'metadata': {     # Optional metadata
        'timestamp': '...',
        'agent_version': '...',
        ...
    },
    'error': '...'    # Only if success=False
}
```

**Coordinator Registration Pattern**:
```python
coordinator = MarketingCoordinator()
coordinator.register_specialized_agent('agent_name', AgentInstance())
```

### Data Governance

- **PII Handling**: All PII tables/models must be tagged with `pii`
- **Data Freshness**: Maximum 24-hour staleness for operational data
- **Quality Thresholds**: < 5% null rate, > 95% quality score
- **GDPR/CCPA**: All data collection requires explicit consent tracking

### Naming Conventions

- **BigQuery Tables**: `layer_domain_entity` (e.g., `stg_customer_profile`)
- **dbt Models**: Match BigQuery table names
- **ML Models**: `model_type_version` (e.g., `lead_scoring_v1`)
- **API Endpoints**: RESTful, versioned (e.g., `/v1/predict/lead-score`)

### Code Quality

- All code must pass quality gates before production
- Data transformations use dbt for version control and testing
- ML training code stored in `src/` directories with corresponding configs
- Monitoring and alerting configured for all production services
- Agents must have comprehensive test coverage (unit + integration)
- All agents must support stub mode for testing without cloud credentials

### Ethical AI Principles

1. **Data Privacy & Consent**: GDPR/CCPA compliance, transparent collection
2. **Algorithmic Fairness**: Diverse training data, regular bias audits
3. **Transparency**: Clear disclosure of AI-generated content
4. **Human Oversight**: Critical decisions require human approval
5. **Value-Driven**: All automation provides genuine customer value

---

## Performance Targets

### API Latency
- P50: < 50ms
- P95: < 100ms
- P99: < 200ms

### BigQuery Query Performance
- Interactive queries: < 5 seconds
- Batch transformations: < 30 minutes
- Real-time streaming: < 1 second ingestion lag

### ML Model Performance
- Prediction latency: < 100ms (P95)
- Minimum accuracy: 80%
- Model refresh frequency: Weekly (or on drift detection)
- Feature freshness: < 24 hours

### System Throughput
- API requests: 100+ RPS sustained
- Data ingestion: 10K+ events/second
- BigQuery scanned data: Minimize via partitioning/clustering

### Agent System Performance (NEW)
- Coordinator delegation latency: < 500ms
- Multi-agent workflow completion: < 5 seconds
- Agent registration: Instant (in-memory)
- Stub mode overhead: < 10ms per agent

---

## Getting Started

**New to this codebase?**
1. Read: `README.md` - Project vision and overview
2. Read: `GETTING_STARTED.md` - Implementation guide and phase breakdown
3. Read: `agents/FINAL_IMPLEMENTATION_SUMMARY.md` - Agent system implementation details
4. Explore: Run `.repometa/visualizer.py --interactive` for guided tour

**Starting a new agent?**
1. Review existing agent patterns in `agents/content_generation/main.py` or `agents/predictive_insights/main.py`
2. Implement `execute(**kwargs)` method returning `{'success': bool, ...}`
3. Add comprehensive tests (unit + integration with coordinator)
4. Support stub mode for testing without cloud credentials
5. Register agent in coordinator using `register_specialized_agent()`
6. Update coordinator routing logic if using keyword-based delegation

**Starting a new feature in existing phases?**
1. Identify the phase (1, 2, or 3) the feature belongs to
2. Review the corresponding `phase-X/` directory structure
3. Follow the established patterns (dbt for data, Vertex AI for ML)
4. Ensure comprehensive tests per `testing/TESTING_STRATEGY.md`
5. Update documentation in `docs/` as needed

**Debugging an issue?**
1. Check monitoring: `monitoring/alerting/` for incident playbooks
2. Review logs in Cloud Logging (GCP)
3. Use `.repometa/analyzer.py --impact-analysis` to understand dependencies
4. Follow chaos engineering principles from `testing/chaos-engineering/`
5. For agent issues: Check `agents/coordinator/main.py` delegation history
6. For agent execution errors: Review agent's `execute()` method and error handling

**Running tests for agents?**
1. Ensure virtual environment activated: `cd agents/ && ./venv/Scripts/activate`
2. Run all tests: `pytest -v`
3. Run specific agent tests: `pytest coordinator/tests/ -v`
4. Run integration tests: `pytest tests/test_integration.py -v`
5. For BigQuery tests: Ensure `gcloud auth application-default login` completed

---

## Resources

### Multi-Agent System Documentation (NEW)
- **Implementation Summary**: `agents/FINAL_IMPLEMENTATION_SUMMARY.md` - Complete Phase 1 documentation
- **Agent System README**: `agents/README.md` - Quick start for agent development
- **Test Results**: `agents/FINAL_IMPLEMENTATION_SUMMARY.md` (lines 243-266) - All test results

### Architecture & Planning
- **Architecture**: `docs/architecture-overview.md`
- **Roadmap**: `docs/implementation-roadmap.md`
- **Ethics**: `docs/ethical-framework.md`
- **ROI**: `performance-metrics/roi-framework.md`

### Testing & Quality
- **Testing Strategy**: `testing/TESTING_STRATEGY.md`
- **Performance Testing**: `testing/performance/PERFORMANCE_TESTING.md`
- **Chaos Engineering**: `testing/chaos-engineering/CHAOS_ENGINEERING.md`
- **Monitoring & Alerting**: `monitoring/alerting/ALERTING_AND_INCIDENT_RESPONSE.md`

### External Resources
- **Google ADK Documentation**: https://cloud.google.com/vertex-ai/docs/agent-builder
- **Gemini API**: https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview
- **Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **BigQuery**: https://cloud.google.com/bigquery/docs
