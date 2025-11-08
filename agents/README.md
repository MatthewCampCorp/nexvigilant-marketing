# NexVigilant Marketing Agent System

AI-powered multi-agent marketing automation system built with Google ADK, integrating with NexVigilant's data infrastructure.

## Architecture

```
Marketing Coordinator Agent (Root)
├── Data Intelligence Agent (BigQuery, dbt)
├── Predictive Insights Agent (Vertex AI Models)
├── Content Generation Agent (Gemini)
├── Campaign Design Agent (Google Ads, DV360)
└── Performance Optimization Agent (GA360, Attribution)
```

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Google Cloud Platform account with billing enabled
- Access to NexVigilant GCP project
- BigQuery, Vertex AI, and Gemini APIs enabled

### Installation

1. **Clone and navigate to agents directory**
```bash
cd C:\Users\campi\nexvigilant-marketing\agents
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your GCP project details
```

5. **Authenticate with GCP**
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Running Agents

**Interactive CLI Mode**
```bash
adk run coordinator
```

**Web Interface**
```bash
adk web
```

**Test Agent Workflows**
```bash
pytest tests/ -v
```

## Project Structure

```
agents/
├── coordinator/              # Root coordinator agent
│   ├── main.py              # Coordinator logic
│   ├── prompts.py           # Agent instructions
│   ├── tools.py             # Tool registry
│   └── tests/
├── data_intelligence/       # BigQuery & dbt integration
│   ├── main.py
│   ├── bigquery_tool.py
│   ├── dbt_tool.py
│   └── tests/
├── content_generation/      # Gemini content creation
│   ├── main.py
│   ├── gemini_tool.py
│   └── tests/
├── predictive_insights/     # Vertex AI models
│   ├── main.py
│   ├── vertex_ai_tool.py
│   └── tests/
├── campaign_design/         # Google Marketing Platform
│   ├── main.py
│   ├── google_ads_tool.py
│   └── tests/
├── performance_optimization/ # Analytics & optimization
│   ├── main.py
│   ├── ga360_tool.py
│   └── tests/
├── config/
│   ├── agents.yaml          # Agent configurations
│   └── tools.yaml           # Tool definitions
├── eval/
│   └── conversation.test.json  # Test cases
├── deployment/
│   ├── cloud_run/
│   └── cloud_functions/
├── requirements.txt
├── .env.example
└── README.md
```

## Agent Descriptions

### Coordinator Agent
Routes marketing tasks to specialized agents and aggregates results into unified strategies.

**Capabilities:**
- Task delegation and routing
- Multi-agent workflow orchestration
- Result aggregation and synthesis
- Human-in-the-loop decision points

### Data Intelligence Agent
Queries BigQuery and dbt for customer insights, segmentation, and trend analysis.

**Tools:**
- BigQuery SQL execution
- dbt model queries
- Customer segmentation
- Trend analysis

### Predictive Insights Agent
Accesses Vertex AI models for predictive analytics.

**Tools:**
- Lead scoring predictions
- Churn probability forecasting
- Customer lifetime value (CLV) estimation

### Content Generation Agent
Creates personalized marketing content using Gemini.

**Tools:**
- Email copy generation
- Ad creative writing
- Social media content
- Landing page copy

### Campaign Design Agent
Designs and configures multi-channel campaigns.

**Tools:**
- Google Ads API
- Display & Video 360 API
- Search Ads 360 API
- Campaign blueprint creation

### Performance Optimization Agent
Analyzes campaign performance and provides optimization recommendations.

**Tools:**
- Google Analytics 360 API
- BigQuery attribution data
- A/B test analysis
- Budget allocation optimization

## Development Workflow

### Adding a New Agent

1. Create agent directory: `mkdir -p new_agent/tests`
2. Implement agent in `new_agent/main.py`
3. Define tools in `new_agent/tools.py`
4. Write tests in `new_agent/tests/test_agent.py`
5. Register agent in `config/agents.yaml`
6. Update coordinator delegation logic

### Running Tests

```bash
# All tests
pytest tests/ -v --cov=.

# Specific agent
pytest data_intelligence/tests/ -v

# Integration tests
pytest tests/integration/ -v
```

### Linting & Type Checking

```bash
# Format code
black .
ruff check . --fix

# Type checking
mypy coordinator/ data_intelligence/
```

## Configuration

### Agent Configuration (`config/agents.yaml`)

```yaml
coordinator:
  model: gemini-2.0-flash-exp
  temperature: 0.7
  max_iterations: 10

data_intelligence:
  model: gemini-2.0-flash-exp
  temperature: 0.3
  bigquery_timeout: 30

# ... other agents
```

### Tool Configuration (`config/tools.yaml`)

```yaml
bigquery:
  project_id: ${GOOGLE_CLOUD_PROJECT}
  dataset_gold: ${BIGQUERY_DATASET_GOLD}
  timeout_seconds: 30

vertex_ai:
  endpoints:
    lead_scoring: ${VERTEX_AI_ENDPOINT_LEAD_SCORING}
    churn: ${VERTEX_AI_ENDPOINT_CHURN}
    clv: ${VERTEX_AI_ENDPOINT_CLV}
```

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent Response Time | P95 < 10s | Cloud Monitoring |
| BigQuery Query | < 5s | Query execution logs |
| Content Generation | < 15s | Agent latency tracking |
| End-to-End Workflow | < 60s | Orchestration logs |
| System Uptime | 99.9% | Cloud Run metrics |

## Testing Strategy

- **Unit Tests (50%)**: Individual agent logic and tool functions
- **Integration Tests (30%)**: Multi-agent workflows and API integrations
- **End-to-End Tests (15%)**: Complete marketing campaign creation
- **Performance Tests (5%)**: Latency and throughput validation

## Quality Gates

All code must pass before production deployment:
- ✅ All unit tests pass (100%)
- ✅ Code coverage > 80%
- ✅ Linter and type checking pass
- ✅ Performance tests meet SLAs
- ✅ Security scan passes
- ✅ Manual review approval

## Deployment

### Local Development
```bash
adk run coordinator
```

### Cloud Run Deployment
```bash
cd deployment/cloud_run
gcloud run deploy marketing-agents \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Cloud Functions (Event-Driven)
```bash
cd deployment/cloud_functions
gcloud functions deploy agent-orchestrator \
  --runtime python311 \
  --trigger-topic marketing-events \
  --region us-central1
```

## Monitoring & Alerting

- **Cloud Logging**: All agent interactions logged
- **Cloud Monitoring**: Custom metrics for agent performance
- **Alerting**: P0-P4 severity levels with incident playbooks

## Troubleshooting

### Agent Not Responding
1. Check Cloud Logging for errors
2. Verify GCP authentication: `gcloud auth list`
3. Confirm BigQuery/Vertex AI APIs enabled
4. Review agent configuration in `config/agents.yaml`

### BigQuery Timeout
1. Check query complexity in logs
2. Verify partitioning and clustering
3. Increase timeout in `.env`
4. Optimize query in dbt models

### Model Prediction Errors
1. Verify Vertex AI endpoint is deployed
2. Check model input schema
3. Review prediction payload in logs
4. Test endpoint independently

## Resources

- **ADK Documentation**: https://google.github.io/adk-docs/
- **NexVigilant Architecture**: ../docs/architecture-overview.md
- **Testing Strategy**: ../testing/TESTING_STRATEGY.md
- **Ethical Framework**: ../docs/ethical-framework.md

## License
Proprietary - NexVigilant Marketing

---

**Version**: 1.0.0
**Status**: Phase 1 - Foundation
**Last Updated**: 2025-01-08
