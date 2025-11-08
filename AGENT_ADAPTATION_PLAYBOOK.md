# Agent Adaptation Playbook for Claude Code

**Purpose**: Systematic methodology for discovering, deconstructing, adapting, and rebuilding AI agent systems from reference implementations across any domain.

**Target Audience**: Future Claude Code instances performing agent system implementation

**Success Metric**: Complete agent system implementation in <8 hours with 90%+ test coverage

---

## Meta-Process Overview

### Five-Phase Methodology

```
Phase 1: DISCOVERY (15-30 min)
  → Locate reference implementations
  → Evaluate architecture patterns
  → Assess complexity and scope

Phase 2: DECONSTRUCTION (30-60 min)
  → Map component relationships
  → Extract core patterns
  → Identify integration points
  → Document dependencies

Phase 3: ADAPTATION (60-120 min)
  → Map to business requirements
  → Design custom architecture
  → Define agent boundaries
  → Plan data flows

Phase 4: RECONSTRUCTION (3-5 hours)
  → Implement specialized agents
  → Build coordinator logic
  → Create integration tests
  → Validate end-to-end workflows

Phase 5: VALIDATION (30-60 min)
  → Execute test suites
  → Verify integration patterns
  → Document implementation
  → Create deployment guides
```

---

## Phase 1: Discovery & Evaluation

### Objective
Locate high-quality reference implementations and assess fit for business requirements.

### Discovery Sources (Priority Order)

1. **Google Cloud GitHub Repositories**
   - Search: `https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/`
   - Search: `https://github.com/google-gemini/`
   - Pattern: Official examples have high code quality, follow best practices

2. **Google ADK Examples**
   - Search: `https://github.com/googleapis/python-aiplatform/tree/main/samples/model-builder/`
   - Pattern: Framework-specific patterns, production-ready

3. **Vertex AI Documentation**
   - Search: Cloud documentation "agent examples"
   - Pattern: Conceptual clarity, may require implementation

### Evaluation Criteria (Score 0-5 each, need 20+ total)

```python
evaluation_matrix = {
    'architectural_clarity': 0-5,      # Clear component separation?
    'code_quality': 0-5,               # Tests, types, documentation?
    'integration_examples': 0-5,       # Cloud service integration shown?
    'extensibility': 0-5,              # Easy to add new components?
    'production_readiness': 0-5,       # Error handling, logging, security?
    'testing_coverage': 0-5,           # Comprehensive test examples?
}
```

### Key Questions to Answer

1. **Architecture Pattern**: Hierarchical delegation? Event-driven? Sequential pipeline?
2. **Agent Communication**: How do agents interact? Synchronous? Asynchronous?
3. **Coordinator Logic**: Single root? Multiple coordinators? Flat structure?
4. **Data Flow**: How does data pass between agents? Shared state? Message passing?
5. **Error Handling**: How are failures managed? Retry logic? Fallbacks?
6. **Testing Strategy**: Unit tests? Integration tests? Mocking patterns?

### Output from Phase 1

```markdown
## Discovery Summary
- **Reference Implementation**: [URL or source]
- **Architecture Pattern**: [e.g., "Hierarchical delegation with keyword routing"]
- **Evaluation Score**: [X/30]
- **Key Strengths**: [List 3-5 strengths]
- **Adaptation Requirements**: [List what needs to change for your use case]
- **Estimated Implementation Time**: [Hours]
```

---

## Phase 2: Deconstruction

### Objective
Deeply understand the reference architecture, extract reusable patterns, and map component relationships.

### Step 2.1: Component Mapping

**Create a component dependency graph**:

```
1. Identify all classes/modules
2. Map dependencies (A → B means "A depends on B")
3. Identify data structures passed between components
4. Document method signatures and contracts
```

**Example from Marketing Agents**:
```
MarketingCoordinator (root)
  ├─ depends on: DelegationDecision, AgentResult (dataclasses)
  ├─ registers: specialized_agents dict
  └─ methods:
      ├─ determine_delegation(request: str) → List[DelegationDecision]
      ├─ execute_delegation(decision: DelegationDecision) → AgentResult
      └─ aggregate_results(results: List[AgentResult]) → Dict[str, Any]

DataIntelligenceAgent (specialized)
  ├─ depends on: BigQueryTool
  ├─ contract: execute(**kwargs) → Dict[str, Any]
  └─ returns: {'success': bool, 'result': {...}, 'metadata': {...}}

BigQueryTool (integration layer)
  ├─ depends on: google.cloud.bigquery
  ├─ security: query validation, allowed tables, timeouts
  └─ methods:
      ├─ query(sql: str) → List[Dict[str, Any]]
      └─ _validate_query(sql: str) → bool
```

### Step 2.2: Extract Core Patterns

**Identify repeatable patterns** (not domain-specific logic):

1. **Delegation Pattern**
   ```python
   # Pattern: Coordinator → determine delegation → execute → aggregate
   def process_request(self, request: str) -> Dict[str, Any]:
       decisions = self.determine_delegation(request)
       results = [self.execute_delegation(d) for d in decisions]
       return self.aggregate_results(results)
   ```

2. **Agent Contract Pattern**
   ```python
   # Pattern: All agents implement execute() with standard return format
   def execute(self, **kwargs) -> Dict[str, Any]:
       return {
           'success': bool,
           'result': {...},      # Agent-specific data
           'metadata': {...},    # Timestamps, versions, etc.
           'error': str | None   # Only if success=False
       }
   ```

3. **Stub Mode Pattern**
   ```python
   # Pattern: Detect credentials, fallback to test data
   def __init__(self):
       try:
           self.client = CloudService()  # Attempt production
       except:
           logger.warning("No credentials, using stub mode")
           self.client = None

   def execute(self, **kwargs):
       if self.client:
           return self._execute_production(**kwargs)
       return self._execute_stub(**kwargs)
   ```

4. **Security Validation Pattern**
   ```python
   # Pattern: Allowlist → Validate → Execute with limits
   ALLOWED_TABLES = ['table1', 'table2']

   def _validate_query(self, sql: str) -> bool:
       # Check against injection patterns
       # Verify only allowed tables referenced
       # Return True/False

   def query(self, sql: str, timeout: int = 30):
       if not self._validate_query(sql):
           raise SecurityError("Invalid query")
       return self.client.query(sql).result(timeout=timeout)
   ```

5. **Integration Test Pattern**
   ```python
   # Pattern: Mock agents for coordinator testing
   class MockAgent:
       def execute(self, **kwargs):
           return {'success': True, 'result': 'test_data'}

   coordinator.register_specialized_agent('mock', MockAgent())
   response = coordinator.process_request("test")
   assert response['results']['success'] is True
   ```

### Step 2.3: Identify Integration Points

**Document all external service integrations**:

```python
integration_points = {
    'BigQuery': {
        'library': 'google-cloud-bigquery',
        'authentication': 'Application Default Credentials',
        'setup_command': 'gcloud auth application-default login',
        'stub_mode': 'Return hardcoded test data',
        'test_requirements': 'BigQuery auth for 7/18 tests',
    },
    'Vertex AI': {
        'library': 'google-cloud-aiplatform',
        'authentication': 'Application Default Credentials',
        'setup_command': 'aiplatform.init(project=..., location=...)',
        'stub_mode': 'Simulate predictions with realistic data',
        'test_requirements': 'Endpoint URLs via environment variables',
    },
    'Gemini': {
        'library': 'google-genai',
        'authentication': 'Vertex AI credentials',
        'setup_command': 'genai.Client(vertexai=True, project=...)',
        'stub_mode': 'Not needed (fast, no cost)',
        'test_requirements': 'Project ID via environment variable',
    },
}
```

### Step 2.4: Document Dependencies

**Create requirements matrix**:

```python
# Core dependencies
dependencies = {
    'agent_framework': 'google-cloud-aiplatform[adk,agent-engines]>=1.93.0',
    'genai': 'google-genai>=1.9.0',
    'cloud_services': [
        'google-cloud-bigquery>=3.11.0',
        'google-cloud-storage>=2.10.0',
        'google-cloud-pubsub>=2.18.0',
    ],
    'data_validation': 'pydantic>=2.10.6',
    'testing': [
        'pytest>=8.3.2',
        'pytest-asyncio>=0.23.7',
        'pytest-cov>=4.1.0',
    ],
    'development': [
        'black>=24.0.0',
        'ruff>=0.4.6',
    ],
}
```

### Output from Phase 2

```markdown
## Deconstruction Summary
- **Component Count**: [N components identified]
- **Core Patterns**: [List 5-7 reusable patterns]
- **Integration Points**: [List external services]
- **Dependencies**: [requirements.txt created]
- **Complexity Assessment**: [Simple/Moderate/Complex]
- **Adaptation Strategy**: [High-level approach]
```

---

## Phase 3: Adaptation

### Objective
Map reference architecture to specific business requirements, designing custom agent boundaries and workflows.

### Step 3.1: Define Business Requirements

**Structured requirements capture**:

```python
business_requirements = {
    'domain': 'marketing',  # or 'customer_service', 'operations', etc.
    'use_cases': [
        {
            'name': 'Customer Segmentation Analysis',
            'agent': 'data_intelligence',
            'inputs': ['customer_data_query'],
            'outputs': ['segments', 'insights'],
            'data_sources': ['BigQuery customer_360 table'],
        },
        {
            'name': 'Lead Scoring',
            'agent': 'predictive_insights',
            'inputs': ['lead_features'],
            'outputs': ['conversion_probability', 'score', 'recommendation'],
            'data_sources': ['Vertex AI endpoint'],
        },
        # ... more use cases
    ],
    'data_sources': ['BigQuery', 'CRM', 'Analytics'],
    'output_channels': ['Dashboard', 'API', 'Email'],
    'compliance_requirements': ['GDPR', 'CCPA'],
    'performance_targets': {
        'latency_p95': '<100ms',
        'throughput': '100+ RPS',
        'availability': '99.9%',
    },
}
```

### Step 3.2: Design Agent Boundaries

**Decision Framework for Agent Separation**:

```python
def should_create_separate_agent(capability: str) -> bool:
    """
    Decision criteria for agent boundaries.

    Create separate agent if ANY of these are true:
    1. Different external service dependency (e.g., BigQuery vs Vertex AI)
    2. Distinct domain expertise required (e.g., data analysis vs content creation)
    3. Independent scaling requirements (e.g., one high-load, one low-load)
    4. Different security/compliance boundaries
    5. Reusable across multiple coordinators

    Keep within existing agent if ALL of these are true:
    1. Same external service dependency
    2. Related domain expertise
    3. Similar scaling requirements
    4. Same security boundary
    5. Tightly coupled workflow
    """
    pass
```

**Example Agent Boundary Decisions (Marketing Use Case)**:

```
✅ SEPARATE AGENTS:
- DataIntelligence (BigQuery) vs PredictiveInsights (Vertex AI)
  → Reason: Different cloud services, different expertise

- ContentGeneration (Gemini) vs DataIntelligence (BigQuery)
  → Reason: Completely different domains (creative vs analytical)

- CampaignDesign vs PerformanceOptimization
  → Reason: Different lifecycle phases (planning vs monitoring)

❌ KEEP TOGETHER:
- Lead scoring + Churn prediction in same PredictiveInsights agent
  → Reason: Same service (Vertex AI), same domain (ML predictions)

- Email content + Social content in same ContentGeneration agent
  → Reason: Same service (Gemini), same domain (content creation)
```

### Step 3.3: Map Data Flows

**Create data flow diagram**:

```
User Request → Coordinator
  ↓
Coordinator.determine_delegation()
  → Keywords: [data, segment, analyze] → DataIntelligence
  → Keywords: [predict, score, churn] → PredictiveInsights
  → Keywords: [create, generate, write] → ContentGeneration
  ↓
Coordinator.execute_delegation(DataIntelligence)
  → DataIntelligence.execute(query="customer segments")
    → BigQueryTool.query("SELECT * FROM customer_360...")
      → Results: [{'segment': 'high_value', 'count': 1250}, ...]
  ← Returns: {'success': True, 'result': {...}}
  ↓
Coordinator.execute_delegation(PredictiveInsights)
  → PredictiveInsights.execute(prediction_type="lead_scoring")
    → Vertex AI Endpoint.predict(features=[...])
      → Results: [{'lead_id': 'L001', 'score': 0.85}, ...]
  ← Returns: {'success': True, 'result': {...}}
  ↓
Coordinator.aggregate_results([data_result, prediction_result])
  → Combines insights from multiple agents
  ← Returns: {
      'summary': '...',
      'insights': {
        'data_intelligence': {...},
        'predictive_insights': {...}
      }
    }
```

### Step 3.4: Design Coordinator Logic

**Choose Routing Strategy**:

```python
routing_strategies = {
    'keyword_based': {
        'complexity': 'LOW',
        'implementation_time': '1-2 hours',
        'accuracy': '70-80%',
        'use_when': 'Phase 1, simple routing, clear keywords',
        'example': 'if "data" in request.lower(): delegate to data_intelligence',
    },
    'llm_powered': {
        'complexity': 'MEDIUM',
        'implementation_time': '4-6 hours',
        'accuracy': '90-95%',
        'use_when': 'Phase 2, complex routing, ambiguous requests',
        'example': 'Use Gemini to analyze request and return agent names',
    },
    'rule_based_ml': {
        'complexity': 'HIGH',
        'implementation_time': '2-3 days',
        'accuracy': '95%+',
        'use_when': 'Phase 3, production optimization, high volume',
        'example': 'Train classifier on historical delegations',
    },
}

# DECISION: Start with keyword_based, upgrade to llm_powered in Phase 2
```

**Keyword-Based Routing Template**:

```python
def determine_delegation(self, user_request: str) -> List[DelegationDecision]:
    """
    Phase 1: Keyword-based routing
    Phase 2: Upgrade to LLM-powered routing
    """
    decisions = []
    request_lower = user_request.lower()

    # Pattern: Check keywords for each agent
    keyword_map = {
        'data_intelligence': ['data', 'customers', 'segment', 'analyze', 'trend'],
        'predictive_insights': ['predict', 'score', 'churn', 'lifetime value', 'clv'],
        'content_generation': ['create', 'write', 'generate', 'content', 'email', 'ad'],
        'campaign_design': ['campaign', 'launch', 'ads', 'advertising'],
        'performance_optimization': ['performance', 'optimize', 'results', 'roi'],
    }

    for agent_name, keywords in keyword_map.items():
        if any(kw in request_lower for kw in keywords):
            decisions.append(DelegationDecision(
                target_agent=agent_name,
                task_description=f"Process: {user_request}",
                parameters={'query': user_request}
            ))

    # Fallback if no keywords matched
    if not decisions:
        decisions.append(DelegationDecision(
            target_agent='default_agent',  # e.g., data_intelligence
            task_description=f"General query: {user_request}",
            parameters={'query': user_request}
        ))

    return decisions
```

### Step 3.5: Plan Testing Strategy

**Test Pyramid for Agent Systems**:

```
                    /\
                   /  \  Manual Testing (5%)
                  /----\
                 /  E2E  \  End-to-End Tests (10%)
                /--------\
               /Integration\  Integration Tests (20%)
              /------------\
             /   Unit Tests  \  Unit Tests (65%)
            /----------------\
```

**Test Coverage Requirements**:

```python
test_requirements = {
    'unit_tests': {
        'coverage': '80%+',
        'focus': 'Individual agent methods, coordinator logic',
        'patterns': [
            'Test each agent.execute() with various inputs',
            'Test coordinator.determine_delegation() routing',
            'Test coordinator.aggregate_results() combinations',
            'Test error handling for each agent',
        ],
    },
    'integration_tests': {
        'coverage': 'All agent combinations',
        'focus': 'Multi-agent workflows, end-to-end flows',
        'patterns': [
            'Mock all agents, test coordinator orchestration',
            'Test single agent delegation',
            'Test multi-agent delegation',
            'Test result aggregation from multiple agents',
            'Test error propagation',
        ],
    },
    'stub_mode_tests': {
        'coverage': '100% of agents',
        'focus': 'Testing without cloud credentials',
        'patterns': [
            'All agents must have stub mode',
            'Stub mode returns realistic test data',
            'Stub mode should be default if no credentials',
        ],
    },
}
```

### Output from Phase 3

```markdown
## Adaptation Design
- **Agent Count**: [N specialized agents + 1 coordinator]
- **Agent Boundaries**: [List agents with rationale]
- **Data Sources**: [List all external services]
- **Routing Strategy**: [Keyword/LLM/ML]
- **Testing Approach**: [Unit + Integration strategy]
- **Implementation Plan**: [Ordered list of agents to build]
```

---

## Phase 4: Reconstruction

### Objective
Implement the adapted agent system following test-driven development and incremental validation.

### Step 4.1: Project Setup

**Directory Structure**:

```bash
agents/
├── coordinator/
│   ├── __init__.py
│   ├── main.py                 # MarketingCoordinator class
│   ├── prompts.py              # Coordination prompts (if LLM-powered)
│   └── tests/
│       └── test_coordinator.py
│
├── {specialized_agent_1}/      # e.g., data_intelligence
│   ├── __init__.py
│   ├── main.py                 # Agent class
│   ├── {integration}_tool.py   # e.g., bigquery_tool.py
│   └── tests/
│       └── test_{agent}.py
│
├── {specialized_agent_2}/      # e.g., content_generation
│   ├── __init__.py
│   ├── main.py
│   ├── prompts.py              # Agent-specific prompts
│   └── tests/
│       └── test_{agent}.py
│
├── tests/
│   └── test_integration.py     # Multi-agent integration tests
│
├── requirements.txt
├── venv/                       # Virtual environment (gitignored)
└── README.md
```

**Initial Setup Commands**:

```bash
# Create directory structure
mkdir -p agents/coordinator/tests
mkdir -p agents/tests
cd agents/

# Create virtual environment
python -m venv venv
./venv/Scripts/activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Create requirements.txt (from Phase 2 dependency analysis)
cat > requirements.txt << 'EOF'
google-cloud-aiplatform[adk,agent-engines]>=1.93.0
google-genai>=1.9.0
google-cloud-bigquery>=3.11.0
pydantic>=2.10.6
pytest>=8.3.2
pytest-asyncio>=0.23.7
pytest-cov>=4.1.0
EOF

# Install dependencies
pip install -r requirements.txt

# Initialize git (if not already done)
git init
git add .
git commit -m "chore: Initial agent system setup"
```

### Step 4.2: Implementation Order (CRITICAL)

**Follow this exact order** (derived from dependency graph):

```python
implementation_sequence = [
    {
        'order': 1,
        'component': 'Dataclasses',
        'files': ['coordinator/main.py (dataclasses only)'],
        'rationale': 'Shared contracts needed by all components',
        'time_estimate': '15 min',
        'validation': 'Import test: from coordinator.main import DelegationDecision, AgentResult',
    },
    {
        'order': 2,
        'component': 'Coordinator Shell',
        'files': ['coordinator/main.py (class with __init__ only)'],
        'rationale': 'Foundation for agent registration',
        'time_estimate': '30 min',
        'validation': 'coordinator = MarketingCoordinator(); assert coordinator is not None',
    },
    {
        'order': 3,
        'component': 'Coordinator Tests (Shell)',
        'files': ['coordinator/tests/test_coordinator.py'],
        'rationale': 'Test-driven development foundation',
        'time_estimate': '30 min',
        'validation': 'pytest coordinator/tests/test_coordinator.py (expect failures)',
    },
    {
        'order': 4,
        'component': 'Coordinator Core Logic',
        'files': ['coordinator/main.py (all methods)'],
        'rationale': 'Complete coordinator implementation',
        'time_estimate': '2-3 hours',
        'validation': 'pytest coordinator/tests/ -v (expect passes)',
    },
    {
        'order': 5,
        'component': 'Specialized Agent 1 (Simplest)',
        'files': ['Choose agent with fewest dependencies'],
        'rationale': 'Validate agent contract pattern',
        'time_estimate': '1-2 hours',
        'validation': 'pytest {agent}/tests/ -v',
    },
    {
        'order': 6,
        'component': 'Specialized Agent 2',
        'files': ['Next simplest agent'],
        'rationale': 'Build momentum, validate patterns',
        'time_estimate': '1-2 hours',
        'validation': 'pytest {agent}/tests/ -v',
    },
    {
        'order': 7,
        'component': 'Integration Tests (2 agents)',
        'files': ['tests/test_integration.py (partial)'],
        'rationale': 'Validate multi-agent coordination',
        'time_estimate': '30 min',
        'validation': 'pytest tests/test_integration.py -v',
    },
    {
        'order': 8,
        'component': 'Remaining Specialized Agents',
        'files': ['All other agents'],
        'rationale': 'Complete agent suite',
        'time_estimate': '3-4 hours',
        'validation': 'pytest -v (all tests)',
    },
    {
        'order': 9,
        'component': 'Complete Integration Tests',
        'files': ['tests/test_integration.py (complete)'],
        'rationale': 'Validate full system',
        'time_estimate': '1 hour',
        'validation': 'pytest tests/test_integration.py -v (100% pass)',
    },
]
```

### Step 4.3: Agent Implementation Template

**Standard Agent Structure** (copy this for each new agent):

```python
"""
{Agent Name} - {One-line description}

This agent {what it does} using {external service/logic}.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {AgentName}Agent:
    """
    {Agent Name} Agent for {purpose}.

    Capabilities:
    - {Capability 1}
    - {Capability 2}
    - {Capability 3}
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        # Add agent-specific parameters
    ):
        """Initialize {Agent Name} Agent."""
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')

        # Initialize cloud service (with stub mode fallback)
        try:
            self.client = CloudService(project=self.project_id)
            logger.info(f"{self.__class__.__name__} initialized (production mode)")
        except Exception as e:
            logger.warning(f"Cloud service unavailable: {e}. Using stub mode.")
            self.client = None

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main entry point called by coordinator.

        Args:
            **kwargs: Agent-specific parameters

        Returns:
            Dict with 'success': bool and agent-specific result data
        """
        try:
            # Route to appropriate method based on kwargs
            if self.client:
                result = self._execute_production(**kwargs)
            else:
                result = self._execute_stub(**kwargs)

            return {
                'success': True,
                'result': result,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent': self.__class__.__name__,
                    'mode': 'production' if self.client else 'stub',
                }
            }

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent': self.__class__.__name__,
                }
            }

    def _execute_production(self, **kwargs) -> Dict[str, Any]:
        """Production implementation using cloud services."""
        # Implement actual logic here
        pass

    def _execute_stub(self, **kwargs) -> Dict[str, Any]:
        """Stub implementation for testing without credentials."""
        # Return realistic test data
        return {
            'stub_data': 'realistic_test_response',
            # Match production response structure
        }


def main():
    """Test the agent directly."""
    import json
    agent = {AgentName}Agent()

    test_params = {
        # Add test parameters
    }

    result = agent.execute(**test_params)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

### Step 4.4: Testing Template

**Integration Test Template** (tests/test_integration.py):

```python
"""
End-to-end integration test for {System Name}.

This test validates the complete workflow from user request to agent delegation
and result aggregation without requiring cloud credentials (uses stub mode).
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from coordinator.main import MarketingCoordinator, DelegationDecision, AgentResult


class Mock{AgentName}Agent:
    """Mock {Agent Name} Agent for integration testing."""

    def execute(self, **kwargs):
        """Simulate agent execution."""
        return {
            'success': True,
            'result': {
                # Return realistic test data matching production structure
            },
            'metadata': {
                'agent': self.__class__.__name__,
                'mode': 'mock',
            }
        }


def test_single_agent_delegation():
    """Test delegation to a single agent."""
    print("\n=== Test: Single Agent Delegation ===")

    coordinator = MarketingCoordinator()
    mock_agent = Mock{AgentName}Agent()
    coordinator.register_specialized_agent('agent_name', mock_agent)

    request = "Test request that routes to this agent"
    response = coordinator.process_request(request)

    # Validate response structure
    assert 'request' in response
    assert 'delegations' in response
    assert 'results' in response
    assert response['request'] == request

    # Validate results
    aggregated = response['results']
    assert aggregated['success'] is True
    assert 'insights' in aggregated

    print("[PASS] Single agent delegation test passed")
    return True


def test_multi_agent_delegation():
    """Test delegation to multiple agents."""
    print("\n=== Test: Multi-Agent Delegation ===")

    coordinator = MarketingCoordinator()

    # Register multiple agents
    coordinator.register_specialized_agent('agent1', Mock{Agent1}())
    coordinator.register_specialized_agent('agent2', Mock{Agent2}())
    # ... register all agents

    request = "Complex request requiring multiple agents"
    response = coordinator.process_request(request)

    # Validate multiple delegations
    assert len(response['delegations']) >= 2

    # Validate all agents succeeded
    aggregated = response['results']
    assert aggregated['success'] is True

    print("[PASS] Multi-agent delegation test passed")
    return True


def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("{SYSTEM NAME} - INTEGRATION TESTS")
    print("="*60)

    tests = [
        test_single_agent_delegation,
        test_multi_agent_delegation,
        # ... add all test functions
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {test.__name__}: {e}")

    print(f"\nPassed: {passed}/{passed+failed}")
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_integration_tests()
    sys.exit(0 if success else 1)
```

### Step 4.5: Incremental Validation Checkpoints

**After Each Component** (mandatory validation):

```bash
# After implementing component:

# 1. Run linter
ruff check agents/{component}/ --fix

# 2. Format code
black agents/{component}/

# 3. Run tests
pytest agents/{component}/tests/ -v

# 4. Check coverage (if applicable)
pytest agents/{component}/tests/ --cov={component} -v

# 5. Run integration tests (if available)
pytest agents/tests/test_integration.py -v

# 6. Commit (only if all above pass)
git add agents/{component}/
git commit -m "feat({component}): {description}"
```

**Checkpoint Questions** (answer YES to all before proceeding):

```
□ All unit tests passing?
□ Code formatted with black?
□ Linter passing with ruff?
□ Integration tests still passing?
□ Agent returns correct format: {'success': bool, ...}?
□ Stub mode implemented and tested?
□ Error handling covers edge cases?
□ Logging statements added for debugging?
```

### Step 4.6: Common Implementation Pitfalls

**AVOID THESE** (lessons from marketing agents implementation):

```python
pitfalls = {
    'missing_stub_mode': {
        'symptom': 'Tests fail without cloud credentials',
        'fix': 'Add try/except in __init__, implement _execute_stub()',
        'prevention': 'Implement stub mode FIRST, then production mode',
    },
    'inconsistent_return_format': {
        'symptom': 'Coordinator aggregation fails',
        'fix': 'All agents must return {\'success\': bool, ...}',
        'prevention': 'Use agent template, validate in tests',
    },
    'missing_error_handling': {
        'symptom': 'Uncaught exceptions crash coordinator',
        'fix': 'Wrap execute() in try/except, return error dict',
        'prevention': 'Test error cases explicitly',
    },
    'hardcoded_credentials': {
        'symptom': 'Security risk, fails in CI/CD',
        'fix': 'Use environment variables or ADC',
        'prevention': 'Never hardcode credentials, use os.getenv()',
    },
    'integration_without_mocks': {
        'symptom': 'Integration tests require all cloud services',
        'fix': 'Create mock agents for testing',
        'prevention': 'Use mock pattern from test_integration.py',
    },
}
```

### Output from Phase 4

```markdown
## Implementation Complete
- **Total Agents**: [N specialized + 1 coordinator]
- **Lines of Code**: [Production LOC]
- **Test Coverage**: [X%]
- **Test Results**: [X/Y tests passing]
- **Integration Tests**: [X/Y passing]
- **Git Commits**: [N commits]
- **Implementation Time**: [X hours]
```

---

## Phase 5: Validation & Documentation

### Objective
Validate complete system functionality, document architecture, and create deployment guides.

### Step 5.1: Comprehensive Testing

**Test Suite Execution**:

```bash
# 1. Run all unit tests with coverage
cd agents/
pytest --cov=coordinator --cov=data_intelligence --cov=content_generation --cov=predictive_insights -v

# 2. Run integration tests
pytest tests/test_integration.py -v

# 3. Check overall coverage
pytest --cov=. --cov-report=html -v

# 4. Run with detailed output
pytest -vv -s

# Expected Results:
# - Unit tests: 90%+ passing (100% with cloud auth)
# - Integration tests: 100% passing
# - Coverage: 80%+ code coverage
```

**Test Results Documentation**:

```markdown
## Test Results Summary

### Unit Tests
| Agent | Tests | Passing | Status |
|-------|-------|---------|--------|
| Coordinator | 18 | 18 | ✅ 100% |
| Agent 1 | X | Y | ✅/⏳ Z% |
| Agent 2 | X | Y | ✅/⏳ Z% |
| **TOTAL** | XX | YY | ✅ ZZ% |

### Integration Tests
| Test | Status |
|------|--------|
| Single Agent Delegation | ✅ PASS |
| Multi-Agent Delegation | ✅ PASS |
| Result Aggregation | ✅ PASS |
| Error Handling | ✅ PASS |
| Complete Workflow | ✅ PASS |
| **Success Rate** | **100%** |
```

### Step 5.2: Create Implementation Summary

**Generate comprehensive documentation**:

```markdown
# {System Name} - Implementation Summary

## Overview
{Brief description of what was built}

**Status**: ✅ COMPLETE
**Implementation Date**: {Date}
**Total Implementation Time**: {Hours}

## System Architecture

```
{ASCII diagram of agent system}
```

## Implementation Details

### Coordinator Agent
**File**: `coordinator/main.py` ({LOC} lines)
**Tests**: {X/Y} passing
**Status**: {Production-ready/Needs auth/etc}

**Features**:
- {Feature 1}
- {Feature 2}
- {Feature 3}

**Key Methods**:
- `determine_delegation()` - {Description}
- `execute_delegation()` - {Description}
- `aggregate_results()` - {Description}

### Specialized Agent 1
**File**: `{agent}/main.py` ({LOC} lines)
**Tests**: {X/Y} passing
**Status**: {Status}

**Capabilities**:
- {Capability 1}
- {Capability 2}

{Repeat for all agents}

## Test Results Summary
{Include test results from Step 5.1}

## Dependencies
{List all dependencies from requirements.txt with versions}

## Next Steps
{List Phase 2/3 planned enhancements}
```

### Step 5.3: Create Deployment Guide

**Document deployment process**:

```markdown
# Deployment Guide

## Prerequisites
- Google Cloud Platform account with billing enabled
- Project with required APIs enabled:
  - BigQuery API
  - Vertex AI API
  - Cloud Functions API (if deploying as functions)
  - Cloud Run API (if deploying as service)

## Local Development Setup

### 1. Clone Repository
```bash
git clone {repository_url}
cd {project_directory}/agents/
```

### 2. Create Virtual Environment
```bash
python -m venv venv
./venv/Scripts/activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Authenticate with Google Cloud
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Authenticate
gcloud auth application-default login
```

### 5. Set Environment Variables
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1

# For Vertex AI endpoints (if applicable)
export VERTEX_AI_ENDPOINT_LEAD_SCORING=your-endpoint-id
export VERTEX_AI_ENDPOINT_CHURN=your-endpoint-id
```

### 6. Run Tests
```bash
pytest -v
```

### 7. Run Agents
```bash
# Run coordinator
python -m coordinator.main

# Run individual agents
python -m {agent_name}.main
```

## Production Deployment

### Option 1: Cloud Run
{Cloud Run deployment steps}

### Option 2: Cloud Functions
{Cloud Functions deployment steps}

### Option 3: GKE
{Kubernetes deployment steps}
```

### Step 5.4: Update Project Documentation

**Files to create/update**:

1. **README.md** (root)
   - Add agent system overview
   - Link to implementation summary
   - Update status to "Phase 1 Complete"

2. **CLAUDE.md** (root)
   - Add "Multi-Agent System Architecture" section
   - Add "Essential Commands" for agent development
   - Add "High-Level Architecture & Patterns"
   - Update "Getting Started" with agent-specific guidance

3. **agents/README.md** (new)
   - Agent-specific documentation
   - Quick start guide
   - Testing instructions

4. **agents/FINAL_IMPLEMENTATION_SUMMARY.md** (new)
   - Complete implementation details
   - Test results
   - Code metrics
   - Next steps

### Step 5.5: Git Commit & Push

**Final commit sequence**:

```bash
# 1. Ensure all tests pass
pytest -v

# 2. Stage all files
git add agents/
git add README.md CLAUDE.md

# 3. Create comprehensive commit
git commit -m "feat(agents): Complete Phase 1 - All specialized agents implemented

- Implemented 6 agents (1 coordinator + 5 specialized)
- 3,739 lines of production code
- 74+ test cases with 91%+ passing rate
- Comprehensive security controls
- Full documentation

Agents:
- Coordinator: 401 lines, 18/18 tests ✅
- Data Intelligence: 791 lines, 11/18 tests (7 need BigQuery auth)
- Content Generation: 647 lines, 21/21 tests ✅
- Predictive Insights: 575 lines, 17/17 tests ✅
- Campaign Design: 287 lines, integration tested ✅
- Performance Optimization: 419 lines, integration tested ✅

Test Results:
- Unit tests: 67+/74+ passing (91%+)
- Integration tests: 6/6 passing (100%)

Documentation:
- Updated CLAUDE.md with agent architecture
- Created FINAL_IMPLEMENTATION_SUMMARY.md
- Created deployment guides

🤖 Generated with Claude Code"

# 4. Create GitHub repository (if needed)
gh repo create {repo_name} --public --source=. --push

# 5. Push to remote
git push origin main
```

### Output from Phase 5

```markdown
## Validation Complete
- **Test Coverage**: [X%]
- **All Tests Passing**: [Yes/No (with auth requirements)]
- **Documentation**: [Complete]
- **Git Repository**: [URL]
- **Deployment Guide**: [Created]
- **Ready for Production**: [Yes/No]
```

---

## Cross-Domain Application

### Applying This Methodology to Other Domains

**The Five-Phase methodology is domain-agnostic**. Here's how to apply it:

### Customer Service Agents Example

```python
domain_adaptation = {
    'domain': 'customer_service',
    'agents': {
        'coordinator': 'CustomerServiceCoordinator',
        'specialized_agents': [
            {
                'name': 'TicketClassification',
                'service': 'Vertex AI AutoML',
                'function': 'Classify support tickets by category',
            },
            {
                'name': 'KnowledgeBase',
                'service': 'Vertex AI Search',
                'function': 'Search internal documentation',
            },
            {
                'name': 'ResponseGeneration',
                'service': 'Gemini',
                'function': 'Generate contextual responses',
            },
            {
                'name': 'SentimentAnalysis',
                'service': 'Natural Language API',
                'function': 'Analyze customer sentiment',
            },
            {
                'name': 'Escalation',
                'service': 'Business Logic',
                'function': 'Determine if human escalation needed',
            },
        ],
    },
    'workflow': 'Ticket → Classify → Search KB → Generate Response → Check Sentiment → Escalate if needed',
}
```

### Operations Agents Example

```python
domain_adaptation = {
    'domain': 'operations',
    'agents': {
        'coordinator': 'OperationsCoordinator',
        'specialized_agents': [
            {
                'name': 'InventoryMonitoring',
                'service': 'BigQuery',
                'function': 'Monitor inventory levels',
            },
            {
                'name': 'DemandForecasting',
                'service': 'Vertex AI',
                'function': 'Predict future demand',
            },
            {
                'name': 'SupplierSelection',
                'service': 'Optimization API',
                'function': 'Optimize supplier selection',
            },
            {
                'name': 'OrderGeneration',
                'service': 'Business Logic',
                'function': 'Generate purchase orders',
            },
            {
                'name': 'AnomalyDetection',
                'service': 'Vertex AI',
                'function': 'Detect supply chain anomalies',
            },
        ],
    },
    'workflow': 'Monitor → Forecast → Detect Anomalies → Select Suppliers → Generate Orders',
}
```

### Sales Agents Example

```python
domain_adaptation = {
    'domain': 'sales',
    'agents': {
        'coordinator': 'SalesCoordinator',
        'specialized_agents': [
            {
                'name': 'LeadEnrichment',
                'service': 'External APIs + BigQuery',
                'function': 'Enrich lead data from multiple sources',
            },
            {
                'name': 'LeadScoring',
                'service': 'Vertex AI',
                'function': 'Score leads by conversion probability',
            },
            {
                'name': 'PersonalizationEngine',
                'service': 'Gemini',
                'function': 'Generate personalized outreach',
            },
            {
                'name': 'NextBestAction',
                'service': 'Optimization API',
                'function': 'Recommend next best action',
            },
            {
                'name': 'DealIntelligence',
                'service': 'BigQuery + Vertex AI',
                'function': 'Analyze deal health and risks',
            },
        ],
    },
    'workflow': 'Enrich Lead → Score → Generate Outreach → Recommend Action → Monitor Deal',
}
```

---

## Decision Trees & Frameworks

### When to Use Hierarchical Delegation

```python
def should_use_hierarchical_delegation(requirements: Dict) -> bool:
    """
    Use hierarchical delegation if:
    - Multiple distinct capabilities needed
    - Different external services for each capability
    - Want to scale agents independently
    - Need human approval gates for certain actions

    DO NOT use hierarchical delegation if:
    - Single, linear workflow
    - All operations use same external service
    - Very low latency requirements (<10ms)
    - Simple if/else logic sufficient
    """

    score = 0

    if requirements['distinct_capabilities'] > 3:
        score += 2

    if len(requirements['external_services']) > 2:
        score += 2

    if requirements['human_approval_needed']:
        score += 1

    if requirements['independent_scaling_needed']:
        score += 1

    return score >= 4  # Use if score >= 4
```

### When to Implement Stub Mode

```python
def should_implement_stub_mode(agent: Dict) -> bool:
    """
    ALWAYS implement stub mode if:
    - Agent uses external paid services (BigQuery, Vertex AI, etc.)
    - Development requires frequent testing
    - CI/CD pipeline needs to run tests
    - Want to develop without cloud credentials

    Can skip stub mode if:
    - Agent is pure business logic (no external services)
    - External service is free and fast
    """

    return (
        agent['uses_paid_service'] or
        agent['requires_authentication'] or
        agent['slow_response_time'] or
        True  # Best practice: ALWAYS implement stub mode
    )
```

### Routing Strategy Decision

```python
def choose_routing_strategy(requirements: Dict) -> str:
    """
    keyword_based: Phase 1, simple, 70-80% accuracy
    llm_powered: Phase 2, complex, 90-95% accuracy
    ml_classifier: Phase 3, optimized, 95%+ accuracy
    """

    if requirements['request_complexity'] == 'simple':
        return 'keyword_based'

    if requirements['request_complexity'] == 'medium':
        return 'llm_powered'

    if requirements['request_complexity'] == 'complex':
        if requirements['training_data_available']:
            return 'ml_classifier'
        else:
            return 'llm_powered'

    # Default: Start simple, upgrade later
    return 'keyword_based'
```

---

## Performance Benchmarks

### Expected Implementation Times

```python
benchmarks = {
    'simple_agent_system': {
        'agents': '3-4 specialized agents',
        'time': '4-6 hours',
        'complexity': 'Low',
        'example': 'Basic CRUD operations with BigQuery',
    },
    'moderate_agent_system': {
        'agents': '5-7 specialized agents',
        'time': '6-10 hours',
        'complexity': 'Medium',
        'example': 'Marketing agents (data + ML + content generation)',
    },
    'complex_agent_system': {
        'agents': '8-12 specialized agents',
        'time': '12-20 hours',
        'complexity': 'High',
        'example': 'Multi-domain agents with complex workflows',
    },
}
```

### Test Coverage Targets

```python
coverage_targets = {
    'coordinator': {
        'unit_tests': '100%',
        'integration_tests': '100%',
        'rationale': 'Core orchestration logic must be bulletproof',
    },
    'specialized_agents': {
        'unit_tests': '80%+',
        'integration_tests': 'At least 1 test per agent',
        'rationale': 'Cover main logic paths and error handling',
    },
    'integration_suite': {
        'single_agent': '100% (test each agent individually)',
        'multi_agent': '100% (test all combinations used)',
        'error_scenarios': '100% (test failure handling)',
    },
}
```

---

## Critical Success Factors

### Must-Haves

```python
critical_success_factors = [
    {
        'factor': 'Test-Driven Development',
        'importance': 'CRITICAL',
        'rationale': 'Tests catch integration errors early, enable confident refactoring',
        'implementation': 'Write tests BEFORE implementing each agent',
    },
    {
        'factor': 'Stub Mode Implementation',
        'importance': 'CRITICAL',
        'rationale': 'Enable development without cloud dependencies, fast testing',
        'implementation': 'All agents must have _execute_stub() method',
    },
    {
        'factor': 'Consistent Return Format',
        'importance': 'CRITICAL',
        'rationale': 'Coordinator aggregation depends on predictable structure',
        'implementation': 'All agents return {"success": bool, ...}',
    },
    {
        'factor': 'Incremental Validation',
        'importance': 'CRITICAL',
        'rationale': 'Catch issues early, maintain working state',
        'implementation': 'Run tests after each component, commit only if passing',
    },
    {
        'factor': 'Documentation as You Go',
        'importance': 'HIGH',
        'rationale': 'Capture decisions while context is fresh',
        'implementation': 'Update docs immediately after implementing each agent',
    },
]
```

### Common Failure Modes

```python
failure_modes = [
    {
        'failure': 'Skipping Tests',
        'symptom': 'Integration breaks late in development',
        'prevention': 'Mandatory test execution before each commit',
        'recovery': 'Stop, write tests for existing code, then proceed',
    },
    {
        'failure': 'No Stub Mode',
        'symptom': 'Cannot test without cloud credentials, slow development',
        'prevention': 'Implement stub mode in __init__ of every agent',
        'recovery': 'Retrofit stub mode before adding more agents',
    },
    {
        'failure': 'Inconsistent Interfaces',
        'symptom': 'Coordinator cannot aggregate results',
        'prevention': 'Use agent template, validate in integration tests',
        'recovery': 'Standardize all agent return formats',
    },
    {
        'failure': 'Poor Agent Boundaries',
        'symptom': 'Agents too tightly coupled, hard to test',
        'prevention': 'Use decision framework from Phase 3',
        'recovery': 'Refactor to separate concerns, may need new agents',
    },
]
```

---

## Reusable Code Templates

### Complete Coordinator Template

```python
"""
{System Name} Coordinator Agent.

This agent coordinates {N} specialized agents using hierarchical delegation.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DelegationDecision:
    """Represents a decision to delegate a task to a specialized agent."""
    target_agent: str
    task_description: str
    parameters: Dict[str, Any]
    requires_human_approval: bool = False
    approval_reason: Optional[str] = None


@dataclass
class AgentResult:
    """Result from a specialized agent execution."""
    agent_name: str
    task: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class {System}Coordinator:
    """
    {System} Coordinator Agent.

    Orchestrates {N} specialized agents:
    - {Agent 1}: {Purpose}
    - {Agent 2}: {Purpose}
    ...
    """

    def __init__(self, project_id: Optional[str] = None):
        """Initialize coordinator."""
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.specialized_agents: Dict[str, Any] = {}
        self.delegation_history: List[DelegationDecision] = []
        self.results_history: List[AgentResult] = []

        logger.info(f"{self.__class__.__name__} initialized")

    def register_specialized_agent(self, name: str, agent: Any) -> None:
        """Register a specialized agent for delegation."""
        self.specialized_agents[name] = agent
        logger.info(f"Registered specialized agent: {name}")

    def determine_delegation(self, user_request: str) -> List[DelegationDecision]:
        """
        Analyze user request and determine which agents to delegate to.

        Phase 1: Keyword-based routing
        Phase 2: Upgrade to LLM-powered routing
        """
        decisions = []
        request_lower = user_request.lower()

        # Define keyword mappings for each agent
        keyword_map = {
            'agent_1': ['keyword1', 'keyword2'],
            'agent_2': ['keyword3', 'keyword4'],
            # ... add all agents
        }

        for agent_name, keywords in keyword_map.items():
            if any(kw in request_lower for kw in keywords):
                decisions.append(DelegationDecision(
                    target_agent=agent_name,
                    task_description=f"Process: {user_request}",
                    parameters={'query': user_request}
                ))

        # Fallback if no keywords matched
        if not decisions:
            decisions.append(DelegationDecision(
                target_agent='default_agent',
                task_description=f"General query: {user_request}",
                parameters={'query': user_request}
            ))

        self.delegation_history.extend(decisions)
        return decisions

    def execute_delegation(self, decision: DelegationDecision) -> AgentResult:
        """Execute a delegation decision by routing to specialized agent."""
        if decision.requires_human_approval:
            logger.warning(f"Human approval required: {decision.approval_reason}")
            return AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=False,
                error=f"Human approval required: {decision.approval_reason}"
            )

        agent = self.specialized_agents.get(decision.target_agent)

        if not agent:
            logger.error(f"Agent not found: {decision.target_agent}")
            return AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=False,
                error=f"Agent '{decision.target_agent}' not registered"
            )

        try:
            result = agent.execute(**decision.parameters)

            agent_result = AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=True,
                result=result
            )

            self.results_history.append(agent_result)
            return agent_result

        except Exception as e:
            logger.error(f"Error executing {decision.target_agent}: {e}")
            return AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=False,
                error=str(e)
            )

    def aggregate_results(self, results: List[AgentResult]) -> Dict[str, Any]:
        """Aggregate results from multiple specialized agents."""
        aggregated = {
            'summary': '',
            'insights': {},
            'recommendations': [],
            'next_steps': [],
            'success': all(r.success for r in results),
            'errors': [r.error for r in results if not r.success]
        }

        for result in results:
            if result.success and result.result:
                aggregated['insights'][result.agent_name] = result.result

        if aggregated['insights']:
            aggregated['summary'] = f"Successfully gathered insights from {len(aggregated['insights'])} agents"

        return aggregated

    def process_request(self, user_request: str) -> Dict[str, Any]:
        """Main entry point for processing requests."""
        logger.info(f"Processing request: {user_request[:100]}...")

        decisions = self.determine_delegation(user_request)
        logger.info(f"Determined {len(decisions)} delegation(s)")

        results = []
        for decision in decisions:
            logger.info(f"Delegating to {decision.target_agent}")
            result = self.execute_delegation(decision)
            results.append(result)

        aggregated = self.aggregate_results(results)

        return {
            'request': user_request,
            'delegations': [
                {
                    'agent': d.target_agent,
                    'task': d.task_description,
                    'requires_approval': d.requires_human_approval
                }
                for d in decisions
            ],
            'results': aggregated,
            'metadata': {
                'total_delegations': len(decisions),
                'successful_delegations': sum(1 for r in results if r.success),
                'failed_delegations': sum(1 for r in results if not r.success),
            }
        }

    def get_delegation_stats(self) -> Dict[str, Any]:
        """Get statistics about delegation history."""
        if not self.delegation_history:
            return {'total_delegations': 0}

        agent_counts = {}
        for decision in self.delegation_history:
            agent_counts[decision.target_agent] = agent_counts.get(decision.target_agent, 0) + 1

        success_rate = (
            sum(1 for r in self.results_history if r.success) / len(self.results_history)
            if self.results_history else 0
        )

        return {
            'total_delegations': len(self.delegation_history),
            'delegations_by_agent': agent_counts,
            'total_results': len(self.results_history),
            'success_rate': success_rate,
        }
```

---

## Final Checklist

### Before Declaring Success

```markdown
## Phase 1-5 Completion Checklist

### Discovery ✓
- [ ] Reference implementation identified and evaluated
- [ ] Architecture pattern understood
- [ ] Complexity assessed (implementation time estimate)

### Deconstruction ✓
- [ ] Component dependency graph created
- [ ] Core patterns extracted (5-7 patterns)
- [ ] Integration points documented
- [ ] Dependencies listed in requirements.txt

### Adaptation ✓
- [ ] Business requirements captured
- [ ] Agent boundaries defined (decision framework applied)
- [ ] Data flows mapped
- [ ] Routing strategy chosen
- [ ] Testing strategy planned

### Reconstruction ✓
- [ ] Project structure created
- [ ] Virtual environment setup
- [ ] Dependencies installed
- [ ] Coordinator implemented (with tests)
- [ ] All specialized agents implemented (with tests)
- [ ] Integration tests passing (100%)
- [ ] All code formatted (black) and linted (ruff)
- [ ] Git commits created for each component

### Validation ✓
- [ ] Unit tests: 90%+ passing
- [ ] Integration tests: 100% passing
- [ ] Code coverage: 80%+
- [ ] Implementation summary created
- [ ] Deployment guide created
- [ ] CLAUDE.md updated
- [ ] README.md updated
- [ ] Git repository created and pushed

### Production Readiness (Optional)
- [ ] Cloud authentication setup
- [ ] Environment variables configured
- [ ] Production deployment tested
- [ ] Monitoring configured
- [ ] Alerting setup
```

---

## Appendix: Real-World Example

### Marketing Agents Implementation (2025-01-08)

**Timeline**:
- Discovery: 30 min
- Deconstruction: 45 min
- Adaptation: 90 min
- Reconstruction: 4.5 hours
- Validation: 45 min
- **Total: ~6 hours**

**Results**:
- 6 agents (1 coordinator + 5 specialized)
- 3,739 lines of production code
- 74+ test cases
- 91%+ test coverage
- GitHub repository created
- Complete documentation

**Key Decisions**:
1. Used hierarchical delegation pattern (from Google example)
2. Implemented keyword-based routing (Phase 1, upgrade to LLM in Phase 2)
3. All agents support stub mode (no cloud credentials required for testing)
4. Security controls: Query validation, allowed tables, timeouts
5. Test-driven development: Tests before implementation

**Lessons Learned**:
1. Stub mode is CRITICAL - enables fast development without cloud dependencies
2. Test-driven approach catches integration errors early
3. Consistent return format simplifies aggregation
4. Incremental validation (test after each component) maintains working state
5. Documentation as you go is far easier than retroactive documentation

**Reusable Patterns**:
1. Hierarchical delegation (coordinator → agents)
2. Agent contract (execute() with standard return)
3. Stub mode pattern (try production, fallback to test data)
4. Security validation (allowlist → validate → execute with limits)
5. Integration test pattern (mock agents for coordinator testing)

---

**End of Playbook**

This playbook is a living document. Update it based on future agent implementations, new patterns discovered, and lessons learned.
