# AgentBuilder Operating Instructions

## What is AgentBuilder?

AgentBuilder is a **meta-agent that generates complete multi-agent systems**. Give it a specification, and it will create a production-ready system with:
- Hierarchical coordinator agent
- Specialized agents (BigQuery, Vertex AI, Gemini AI, or custom logic)
- Integration tests
- Professional documentation
- Requirements and setup instructions

## Quick Start

### 1. Create Your Agent Specification

Create a JSON file defining your agent system:

```json
{
  "system_name": "YourSystemName",
  "domain": "your_domain",
  "agents": [
    {
      "name": "AgentName",
      "service": "Vertex AI | BigQuery | Gemini AI | Business Logic",
      "function": "What this agent does",
      "keywords": ["keyword1", "keyword2"],
      "parameters": ["param1", "param2"]
    }
  ],
  "routing_strategy": "keyword_based",
  "output_path": "../test-agents/your_system/"
}
```

### 2. Generate Your Agent System

**Option A: Command Line**
```bash
cd C:/Users/campi/claude-agents/agentbuilder-agent
python agent.py --spec-file your-spec.json
```

**Option B: Interactive Mode**
```bash
python agent.py --interactive
# Follow the prompts to enter your specification
```

**Option C: Direct Parameters**
```bash
python agent.py \
  --system-name "CustomerService" \
  --domain "customer_service" \
  --agents '[{"name":"TicketClassifier","service":"Vertex AI","function":"Classify support tickets"}]' \
  --output-path "../test-agents/customer_service/"
```

### 3. Use Your Generated System

```bash
# Navigate to generated system
cd ../test-agents/your_system/your_domain

# Set up environment
python -m venv venv
./venv/Scripts/activate  # Windows
# or: source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_integration.py -v

# Use the coordinator
python -m coordinator.main
```

## Specification Guide

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `system_name` | string | PascalCase name for your system | "HealthcareInsights" |
| `domain` | string | Snake_case domain identifier | "healthcare_analytics" |
| `agents` | array | List of specialized agents | See below |
| `routing_strategy` | string | How coordinator routes requests | "keyword_based" |
| `output_path` | string | Where to generate files | "../test-agents/my_system/" |

### Agent Specification

Each agent in the `agents` array requires:

```json
{
  "name": "PatientAnalyzer",           // PascalCase agent name
  "service": "BigQuery",               // Service type (see below)
  "function": "Analyze patient data",  // Clear description
  "keywords": ["analyze", "patient"],  // Routing keywords (optional)
  "parameters": ["query", "cohort"]    // Expected parameters (optional)
}
```

### Supported Services

| Service | Use Case | Example |
|---------|----------|---------|
| **BigQuery** | Data analysis, querying structured data | Customer analytics, reporting |
| **Vertex AI** | ML predictions, model inference | Risk scoring, classification |
| **Gemini AI** | Content generation, NLP tasks | Report writing, summarization |
| **Business Logic** | Custom algorithms, orchestration | Decision engines, workflow logic |

## Complete Example Specifications

### Example 1: Simple Testing Agent
```json
{
  "system_name": "SimpleTest",
  "domain": "simple_test",
  "agents": [
    {
      "name": "TestAgent",
      "service": "Vertex AI",
      "function": "Test functionality",
      "keywords": ["test"]
    }
  ],
  "routing_strategy": "keyword_based",
  "output_path": "../test-agents/simple_test/"
}
```

### Example 2: Healthcare Analytics (4 agents)
```json
{
  "system_name": "HealthcareInsights",
  "domain": "healthcare_analytics",
  "agents": [
    {
      "name": "PatientDataAnalyzer",
      "service": "BigQuery",
      "function": "Analyze patient demographics and health trends",
      "keywords": ["patient", "demographics", "analyze"],
      "parameters": ["query", "time_range", "patient_cohort"]
    },
    {
      "name": "ClinicalRiskPredictor",
      "service": "Vertex AI",
      "function": "Predict clinical risks using ML models",
      "keywords": ["predict", "risk", "readmission"],
      "parameters": ["patient_id", "prediction_type"]
    },
    {
      "name": "MedicalReportGenerator",
      "service": "Gemini AI",
      "function": "Generate clinical documentation",
      "keywords": ["generate", "report", "summary"],
      "parameters": ["patient_id", "report_type"]
    },
    {
      "name": "TreatmentOptimizer",
      "service": "Business Logic",
      "function": "Recommend optimal treatment pathways",
      "keywords": ["treatment", "recommend"],
      "parameters": ["patient_id", "diagnosis"]
    }
  ],
  "routing_strategy": "keyword_based",
  "output_path": "../test-agents/healthcare_insights/"
}
```

### Example 3: Marketing Automation
```json
{
  "system_name": "MarketingEngine",
  "domain": "marketing_automation",
  "agents": [
    {
      "name": "DataIntelligence",
      "service": "BigQuery",
      "function": "Analyze customer behavior and campaign performance",
      "keywords": ["data", "analyze", "customer", "campaign"],
      "parameters": ["query", "date_range"]
    },
    {
      "name": "ContentGenerator",
      "service": "Gemini AI",
      "function": "Generate marketing content and copy",
      "keywords": ["generate", "content", "copy", "email"],
      "parameters": ["content_type", "audience", "tone"]
    },
    {
      "name": "LeadScorer",
      "service": "Vertex AI",
      "function": "Score and prioritize leads",
      "keywords": ["score", "lead", "predict"],
      "parameters": ["lead_id", "scoring_model"]
    }
  ],
  "routing_strategy": "keyword_based",
  "output_path": "../test-agents/marketing_engine/"
}
```

## Generated File Structure

AgentBuilder creates this complete structure:

```
your_system/
└── your_domain/
    ├── __init__.py
    ├── coordinator/
    │   └── main.py              # Orchestrates all agents
    ├── agent1_name/
    │   ├── __init__.py
    │   └── main.py              # Agent implementation
    ├── agent2_name/
    │   ├── __init__.py
    │   └── main.py
    ├── tests/
    │   └── test_integration.py  # Integration tests
    ├── requirements.txt         # Python dependencies
    └── README.md               # Documentation
```

## Key Features

### Implemented Features
- **Rate Limiting**: 200ms delays between Gemini API calls
- **UTF-8 Encoding**: All files use UTF-8 (works on Windows)
- **Graceful Fallbacks**: If Gemini quota is hit, uses template fallbacks
- **Production + Stub Modes**: Works with or without cloud credentials
- **Intelligent Code Generation**: Uses Gemini AI to generate domain-specific logic

### Best Practices

**1. Start Small**
- Begin with 1-2 agents to understand the system
- Test thoroughly before adding more agents
- Example: `test-simple.json` (1 agent)

**2. Agent Count Considerations**
- **1-2 agents**: Fast generation, no quota issues
- **3-4 agents**: May hit quota limits on some calls (graceful fallbacks)
- **5+ agents**: Expect quota limits, consider waiting 60s between runs

**3. Keyword Selection**
- Use 3-7 keywords per agent
- Include synonyms and related terms
- Example: For a patient analyzer, use: `["patient", "analyze", "demographics", "ehr", "health records"]`

**4. Service Selection**

| Choose... | When you need... |
|-----------|------------------|
| BigQuery | Structured data queries, analytics, reporting |
| Vertex AI | ML predictions, classification, scoring |
| Gemini AI | Text generation, summarization, content creation |
| Business Logic | Custom algorithms, decision trees, orchestration |

## Troubleshooting

### Issue: "429 Quota Exceeded"
**Cause**: Too many Gemini API calls in short time
**Solution**:
- Wait 60 seconds before retrying
- System will use fallback templates automatically
- Generated code will still work, just less customized

### Issue: "UnicodeEncodeError"
**Cause**: Windows console encoding issue
**Solution**:
- Already fixed! AgentBuilder uses UTF-8 encoding
- If you still see it, ensure you're using the latest version

### Issue: "Agent not found"
**Cause**: Agent not registered in coordinator
**Solution**:
```python
# In your code:
coordinator = YourCoordinator()
coordinator.register_specialized_agent('agent_name', YourAgent())
```

### Issue: "Test failures"
**Cause**: Missing dependencies or cloud credentials
**Solution**:
```bash
# Ensure virtual environment is activated
./venv/Scripts/activate

# Install all dependencies
pip install -r requirements.txt

# For BigQuery/Vertex AI tests, authenticate:
gcloud auth application-default login
```

## Advanced Usage

### Running Individual Agents

```bash
# Run just the data agent
python -m data_intelligence.main

# Run coordinator with custom request
python -c "
from coordinator.main import YourCoordinator
coord = YourCoordinator()
result = coord.process_request('Your request here')
print(result)
"
```

### Customizing Generated Code

After generation, you can modify:
1. **Agent logic**: Edit `agent_name/main.py`
2. **Routing**: Edit `coordinator/main.py` keyword mappings
3. **Tests**: Add more tests in `tests/test_integration.py`

### Integration with Existing Systems

```python
# Import your generated agents
from your_domain.coordinator.main import YourCoordinator
from your_domain.agent_name.main import YourAgent

# Use in your application
coordinator = YourCoordinator()
coordinator.register_specialized_agent('agent', YourAgent())

result = coordinator.process_request("Your business request")
```

## Performance & Limits

| Metric | Value |
|--------|-------|
| Generation time (1 agent) | ~10-15 seconds |
| Generation time (4 agents) | ~30-60 seconds |
| Gemini API calls per agent | ~8 calls |
| Rate limit delay | 200ms between calls |
| Max agents recommended | 5 agents per run |
| Quota reset | 60 seconds |

## Getting Help

1. **Check logs**: AgentBuilder logs all operations with `INFO:` prefix
2. **Review generated README**: Each system includes usage instructions
3. **Test incrementally**: Run tests after generation to verify
4. **Inspect generated code**: All code is readable and well-documented

## Quick Reference Card

```bash
# Generate from spec file
python agent.py --spec-file my-spec.json

# Interactive mode
python agent.py --interactive

# Direct CLI parameters
python agent.py --system-name "MySystem" --domain "my_domain" \
  --agents '[{"name":"Agent1","service":"Gemini AI","function":"Do stuff"}]'

# After generation
cd ../test-agents/my_system/my_domain
python -m venv venv && ./venv/Scripts/activate
pip install -r requirements.txt
pytest -v
python -m coordinator.main
```

## Architecture Overview

AgentBuilder follows the **Agent Adaptation Playbook** methodology:

```
User Request
     ↓
Coordinator Agent (Hierarchical Delegation)
     ↓
     ├─→ Specialized Agent 1 (BigQuery)
     ├─→ Specialized Agent 2 (Vertex AI)
     ├─→ Specialized Agent 3 (Gemini AI)
     └─→ Specialized Agent 4 (Business Logic)
     ↓
Results Aggregation
     ↓
Unified Response
```

### How It Works

1. **Coordinator receives request** from user
2. **Determines delegation** using keyword-based routing
3. **Executes specialized agents** in parallel or sequence
4. **Aggregates results** into unified response
5. **Returns insights** with metadata and recommendations

### Agent Communication Pattern

All agents implement a standard contract:

```python
def execute(self, **kwargs) -> Dict[str, Any]:
    """
    Main entry point called by coordinator.

    Returns:
        {
            'success': bool,
            'result': {...},  # Agent-specific data
            'metadata': {...}
        }
    """
```

## Version History

### Version 1.0.0 (Current)
- ✅ Rate limiting with 200ms delays
- ✅ UTF-8 encoding for all generated files
- ✅ Graceful quota handling
- ✅ Production + stub modes
- ✅ 4 service types supported
- ✅ Comprehensive test generation
- ✅ Professional documentation

### Roadmap
- 🔄 LLM-powered routing (Phase 2)
- 🔄 ML-based classifier routing
- 🔄 Event-driven triggers
- 🔄 Real-time optimization

---

**AgentBuilder Version**: 1.0.0
**Location**: `C:/Users/campi/claude-agents/agentbuilder-agent/`
**Core Engine**: `C:/Users/campi/nexvigilant-marketing/agents/agent_builder/`
**Generated**: 2025-01-08

---

## Example Walkthrough

Let's create a complete Customer Service agent system from scratch:

### Step 1: Create Specification

Create `customer-service-spec.json`:
```json
{
  "system_name": "CustomerService",
  "domain": "customer_service",
  "agents": [
    {
      "name": "TicketClassifier",
      "service": "Vertex AI",
      "function": "Classify support tickets by category and priority",
      "keywords": ["classify", "ticket", "category", "priority"],
      "parameters": ["ticket_id", "ticket_text"]
    },
    {
      "name": "ResponseGenerator",
      "service": "Gemini AI",
      "function": "Generate personalized customer responses",
      "keywords": ["generate", "response", "reply", "answer"],
      "parameters": ["ticket_id", "context", "tone"]
    },
    {
      "name": "SentimentAnalyzer",
      "service": "Vertex AI",
      "function": "Analyze customer sentiment and urgency",
      "keywords": ["sentiment", "analyze", "mood", "urgency"],
      "parameters": ["ticket_id", "text"]
    }
  ],
  "routing_strategy": "keyword_based",
  "output_path": "../test-agents/customer_service/"
}
```

### Step 2: Generate System

```bash
cd C:/Users/campi/claude-agents/agentbuilder-agent
python agent.py --spec-file customer-service-spec.json
```

**Expected Output**:
```
============================================================
AgentBuilder Claude Agent v1.0.0
============================================================

System Name: CustomerService
Domain: customer_service
Agents: 3
Routing: keyword_based
Output: ../test-agents/customer_service/

Generating agent system...

============================================================
[SUCCESS] Agent System Generated
============================================================

Files created:
  + coordinator/main.py
  + ticketclassifier/main.py
  + responsegenerator/main.py
  + sentimentanalyzer/main.py
  + tests/test_integration.py
  + requirements.txt
  + README.md
```

### Step 3: Set Up Environment

```bash
cd ../test-agents/customer_service/customer_service
python -m venv venv
./venv/Scripts/activate
pip install -r requirements.txt
```

### Step 4: Test the System

```bash
# Run integration tests
pytest tests/test_integration.py -v

# Run coordinator manually
python -m coordinator.main
```

### Step 5: Use in Your Application

```python
from customer_service.coordinator.main import CustomerServiceCoordinator
from customer_service.ticketclassifier.main import TicketClassifierAgent
from customer_service.responsegenerator.main import ResponseGeneratorAgent
from customer_service.sentimentanalyzer.main import SentimentAnalyzerAgent

# Initialize coordinator
coordinator = CustomerServiceCoordinator()

# Register agents
coordinator.register_specialized_agent('ticketclassifier', TicketClassifierAgent())
coordinator.register_specialized_agent('responsegenerator', ResponseGeneratorAgent())
coordinator.register_specialized_agent('sentimentanalyzer', SentimentAnalyzerAgent())

# Process customer request
result = coordinator.process_request(
    "Classify this support ticket and generate a response: Customer is angry about late delivery"
)

print(result)
# Output:
# {
#   'request': '...',
#   'delegations': [
#     {'agent': 'ticketclassifier', 'task': '...'},
#     {'agent': 'sentimentanalyzer', 'task': '...'},
#     {'agent': 'responsegenerator', 'task': '...'}
#   ],
#   'results': {
#     'summary': 'Successfully gathered insights from 3 agents',
#     'insights': {...},
#     'success': True
#   }
# }
```

That's it! You now have a fully functional multi-agent customer service system.

---

**Questions or Issues?**
Check the logs, review the generated README.md, or inspect the generated code - it's all documented and readable!
