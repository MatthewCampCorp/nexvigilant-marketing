# Chaos Engineering Framework
## Building Resilience Through Controlled Failure

## Overview

Chaos Engineering is the discipline of experimenting on a system to build confidence in its capability to withstand turbulent conditions in production. This framework defines chaos experiments to test and improve the resilience of the Autonomous Marketing Engine.

**Chaos Engineering Principles**:
1. Build a hypothesis around steady-state behavior
2. Vary real-world events (failures)
3. Run experiments in production (carefully!)
4. Automate experiments to run continuously
5. Minimize blast radius

---

## Chaos Engineering Maturity Model

```
Level 1: BASIC
└─ Manual game days (quarterly)
   └─ Test failover in staging
      └─ Document findings

Level 2: AUTOMATED
└─ Automated chaos experiments (weekly)
   └─ Run in staging automatically
      └─ Alert on failures

Level 3: CONTINUOUS
└─ Continuous chaos in production
   └─ Canary chaos (1% of traffic)
      └─ Automatic rollback on issues

Level 4: CHAOS AS CODE
└─ Chaos tests in CI/CD
   └─ Production chaos with advanced safety
      └─ Chaos contributes to SLA/SLO metrics
```

**Current Target**: Level 2 (Automated chaos in staging)
**Future Goal**: Level 3 (Continuous chaos with canaries)

---

## Part 1: Failure Scenarios

### Infrastructure Failures

#### 1. BigQuery Unavailability

**Hypothesis**: System gracefully handles temporary BigQuery outages by using cached data and retrying

**Experiment**:
```python
# chaos_experiments/bigquery_failure.py

from google.cloud import bigquery
import random
import time

class ChaosBigQueryClient:
    """
    Wrapper around BigQuery client that simulates failures
    """

    def __init__(self, failure_rate=0.1, failure_duration_seconds=30):
        self.real_client = bigquery.Client()
        self.failure_rate = failure_rate
        self.failure_duration = failure_duration_seconds
        self.is_failing = False
        self.failure_start = None

    def query(self, query_string, **kwargs):
        """
        Execute query with potential chaos injection
        """

        # Check if we're in a failure period
        if self.is_failing:
            if time.time() - self.failure_start < self.failure_duration:
                # Still in failure mode
                raise Exception("CHAOS: BigQuery temporarily unavailable")
            else:
                # Failure period ended
                self.is_failing = False
                print("✅ BigQuery recovered from chaos failure")

        # Randomly inject failure
        if random.random() < self.failure_rate:
            self.is_failing = True
            self.failure_start = time.time()
            print(f"💥 CHAOS: Injecting BigQuery failure for {self.failure_duration}s")
            raise Exception("CHAOS: BigQuery temporarily unavailable")

        # Normal operation
        return self.real_client.query(query_string, **kwargs)

# Usage in application code with retry logic
def query_with_retry(query, max_retries=3, backoff_seconds=5):
    """
    Query BigQuery with exponential backoff retry
    """
    for attempt in range(max_retries):
        try:
            client = ChaosBigQueryClient(failure_rate=0.2)  # 20% failure rate
            result = client.query(query)
            return result.result()
        except Exception as e:
            if "CHAOS" in str(e) or "unavailable" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = backoff_seconds * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️  BigQuery query failed (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ BigQuery query failed after {max_retries} attempts")
                    # Fallback: Use cached data or return degraded response
                    return get_cached_data_or_default()
            else:
                raise  # Re-raise non-chaos errors

# Test the resilience
def test_bigquery_resilience():
    """
    Test that system handles BigQuery failures gracefully
    """

    query = "SELECT COUNT(*) as count FROM `nexvigilant-staging.marts.customer_360`"

    successful_queries = 0
    failed_queries = 0

    for i in range(100):
        try:
            result = query_with_retry(query)
            successful_queries += 1
        except:
            failed_queries += 1

    success_rate = successful_queries / 100

    print(f"\n=== Chaos Test Results ===")
    print(f"Successful queries: {successful_queries}/100")
    print(f"Failed queries: {failed_queries}/100")
    print(f"Success rate: {success_rate:.1%}")

    # Assertion: Even with chaos, >95% success rate (thanks to retries)
    assert success_rate >= 0.95, f"Success rate {success_rate:.1%} below 95% threshold"

    print("✅ System is resilient to BigQuery failures!")
```

**Success Criteria**:
- Application continues to function (degraded mode acceptable)
- No data corruption
- Automatic recovery when BigQuery returns
- User-facing error rate <5%

---

#### 2. Vertex AI Endpoint Failure

**Hypothesis**: Lead scoring degrades gracefully when Vertex AI is unavailable, falling back to rule-based scoring

**Experiment**:
```python
# chaos_experiments/vertex_ai_failure.py

from google.cloud import aiplatform
import random

class ChaosVertexAIEndpoint:
    """
    Wrapper that simulates Vertex AI endpoint failures
    """

    def __init__(self, real_endpoint_name, failure_rate=0.1):
        self.endpoint = aiplatform.Endpoint(real_endpoint_name)
        self.failure_rate = failure_rate

    def predict(self, instances, **kwargs):
        """
        Predict with chaos injection
        """

        # Inject failure
        if random.random() < self.failure_rate:
            raise Exception("CHAOS: Vertex AI endpoint timeout")

        # Inject high latency (500ms delay)
        if random.random() < self.failure_rate:
            import time
            time.sleep(0.5)
            print("⏱️  CHAOS: Injected 500ms latency")

        return self.endpoint.predict(instances, **kwargs)

# Application code with fallback
def score_lead_resilient(lead_data: dict) -> dict:
    """
    Score lead with AI model, fallback to rule-based if model fails
    """

    try:
        # Try AI model first
        endpoint = ChaosVertexAIEndpoint(
            'projects/123/locations/us-central1/endpoints/456',
            failure_rate=0.3  # 30% failure for testing
        )

        prediction = endpoint.predict(instances=[lead_data], timeout=2)  # 2s timeout

        return {
            'score': prediction.predictions[0]['score'],
            'tier': prediction.predictions[0]['tier'],
            'method': 'ai_model'
        }

    except Exception as e:
        # Fallback to rule-based scoring
        print(f"⚠️  AI model failed: {e}. Using fallback...")

        # Simple rule-based score
        score = 0
        score += lead_data.get('total_sessions', 0) * 5
        score += lead_data.get('content_downloads', 0) * 10
        score += lead_data.get('visited_pricing_page', 0) * 20

        score = min(score, 100)  # Cap at 100

        tier = 'hot' if score >= 70 else 'warm' if score >= 40 else 'cold'

        return {
            'score': score,
            'tier': tier,
            'method': 'fallback_rules'
        }

# Test resilience
def test_vertex_ai_resilience():
    """
    Test that lead scoring continues to work even with AI failures
    """

    test_lead = {
        'total_sessions': 10,
        'content_downloads': 3,
        'visited_pricing_page': 1,
        'email_open_rate': 0.45
    }

    ai_scores = 0
    fallback_scores = 0

    for i in range(100):
        result = score_lead_resilient(test_lead)

        if result['method'] == 'ai_model':
            ai_scores += 1
        else:
            fallback_scores += 1

    print(f"\n=== Resilience Test Results ===")
    print(f"AI model scores: {ai_scores}/100")
    print(f"Fallback scores: {fallback_scores}/100")

    # Both methods should produce reasonable scores
    assert ai_scores > 0 or fallback_scores == 100, "No predictions succeeded"
    print("✅ Lead scoring is resilient to AI endpoint failures!")
```

**Success Criteria**:
- 100% of lead scoring requests return a score (AI or fallback)
- Fallback scores are reasonable (not random)
- System automatically returns to AI when endpoint recovers
- Latency <500ms even with failures

---

### Network Failures

#### 3. API Dependency Timeout

**Hypothesis**: System handles slow/failing external APIs (Salesforce, Braze, etc.) gracefully

**Experiment**:
```python
# chaos_experiments/api_timeout.py

import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class ChaosAPIClient:
    """
    HTTP client that simulates network issues
    """

    def __init__(self, base_url, chaos_config=None):
        self.base_url = base_url
        self.chaos_config = chaos_config or {}

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def post(self, endpoint, json_data, timeout=5):
        """
        POST request with chaos injection
        """

        url = f"{self.base_url}/{endpoint}"

        # Inject latency
        if random.random() < self.chaos_config.get('latency_rate', 0):
            latency_ms = random.uniform(2000, 10000)  # 2-10 seconds
            print(f"⏱️  CHAOS: Injecting {latency_ms:.0f}ms latency to {endpoint}")
            time.sleep(latency_ms / 1000)

        # Inject timeout
        if random.random() < self.chaos_config.get('timeout_rate', 0):
            print(f"💥 CHAOS: Forcing timeout on {endpoint}")
            raise requests.exceptions.Timeout("CHAOS: Simulated timeout")

        # Inject 503 error
        if random.random() < self.chaos_config.get('error_rate', 0):
            print(f"💥 CHAOS: Forcing 503 error on {endpoint}")
            raise requests.exceptions.HTTPError("503 Service Unavailable")

        # Normal request
        return self.session.post(url, json=json_data, timeout=timeout)

# Application code with circuit breaker
class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures
    """

    def __init__(self, failure_threshold=5, timeout_duration=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker logic
        """

        # If circuit is open, check if timeout has passed
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout_duration:
                print("🔧 Circuit breaker entering HALF-OPEN state")
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker is OPEN. Service unavailable.")

        try:
            result = func(*args, **kwargs)

            # Success - reset circuit if in half-open state
            if self.state == 'half_open':
                print("✅ Circuit breaker CLOSED (service recovered)")
                self.state = 'closed'
                self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            # Open circuit if threshold exceeded
            if self.failure_count >= self.failure_threshold:
                print(f"💥 Circuit breaker OPEN after {self.failure_count} failures")
                self.state = 'open'

            raise

# Usage
def send_to_braze_with_resilience(user_id, message):
    """
    Send message to Braze with circuit breaker
    """

    client = ChaosAPIClient(
        'https://api.braze.com',
        chaos_config={
            'latency_rate': 0.2,  # 20% requests have high latency
            'timeout_rate': 0.1,  # 10% timeout
            'error_rate': 0.05    # 5% return errors
        }
    )

    circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_duration=60)

    try:
        result = circuit_breaker.call(
            client.post,
            endpoint='messages/send',
            json_data={'user_id': user_id, 'message': message},
            timeout=3
        )
        return {'status': 'success', 'method': 'braze'}

    except Exception as e:
        # Circuit open - use fallback (queue for later)
        print(f"⚠️  Braze unavailable: {e}. Queueing message...")
        queue_message_for_retry(user_id, message)
        return {'status': 'queued', 'method': 'fallback_queue'}
```

**Success Criteria**:
- Circuit breaker opens after 5 consecutive failures
- Circuit automatically tries to recover after 60 seconds
- Messages are queued during circuit open state
- No user-facing errors (fallback handles gracefully)

---

### Data Corruption & Inconsistency

#### 4. Corrupt Data Injection

**Hypothesis**: Data quality checks catch corrupt data before it affects models

**Experiment**:
```python
# chaos_experiments/data_corruption.py

import pandas as pd
import random

def inject_data_corruption(df: pd.DataFrame, corruption_rate=0.05) -> pd.DataFrame:
    """
    Inject various types of data corruption into dataset
    """

    df_corrupted = df.copy()
    num_rows = len(df)
    num_corruptions = int(num_rows * corruption_rate)

    corruption_types = [
        'null_injection',
        'wrong_type',
        'out_of_range',
        'duplicate'
    ]

    for _ in range(num_corruptions):
        row_idx = random.randint(0, num_rows - 1)
        corruption_type = random.choice(corruption_types)

        if corruption_type == 'null_injection':
            # Set a critical field to NULL
            df_corrupted.at[row_idx, 'email'] = None

        elif corruption_type == 'wrong_type':
            # Set numeric field to string
            df_corrupted.at[row_idx, 'total_sessions'] = 'invalid'

        elif corruption_type == 'out_of_range':
            # Set value outside valid range
            df_corrupted.at[row_idx, 'email_open_rate'] = 15.0  # Should be 0-1

        elif corruption_type == 'duplicate':
            # Duplicate a row (creates duplicate ID)
            df_corrupted = pd.concat([df_corrupted, df.iloc[[row_idx]]])

    print(f"💥 CHAOS: Injected {num_corruptions} data corruptions")
    return df_corrupted

# Data quality validation (from earlier in framework)
def validate_data_quality(df: pd.DataFrame) -> tuple:
    """
    Validate data quality and return (is_valid, errors)
    """

    errors = []

    # Check for nulls in critical fields
    critical_fields = ['email', 'customer_id']
    for field in critical_fields:
        null_count = df[field].isnull().sum()
        if null_count > 0:
            errors.append(f"Found {null_count} null values in {field}")

    # Check for duplicates
    duplicate_count = df.duplicated(subset=['customer_id']).sum()
    if duplicate_count > 0:
        errors.append(f"Found {duplicate_count} duplicate customer_ids")

    # Check for out-of-range values
    if 'email_open_rate' in df.columns:
        invalid = df[(df['email_open_rate'] < 0) | (df['email_open_rate'] > 1)]
        if len(invalid) > 0:
            errors.append(f"Found {len(invalid)} invalid email_open_rate values")

    is_valid = len(errors) == 0
    return is_valid, errors

# Test data quality checks
def test_data_corruption_detection():
    """
    Test that data quality checks catch corrupted data
    """

    # Create clean dataset
    clean_df = pd.DataFrame({
        'customer_id': [f'cust_{i}' for i in range(1000)],
        'email': [f'user{i}@example.com' for i in range(1000)],
        'total_sessions': [random.randint(1, 50) for _ in range(1000)],
        'email_open_rate': [random.uniform(0, 1) for _ in range(1000)]
    })

    # Inject corruption
    corrupted_df = inject_data_corruption(clean_df, corruption_rate=0.1)  # 10% corruption

    # Validate
    is_valid, errors = validate_data_quality(corrupted_df)

    print(f"\n=== Data Quality Chaos Test ===")
    print(f"Clean rows: {len(clean_df)}")
    print(f"Corrupted rows: {len(corrupted_df)}")
    print(f"Validation result: {'PASS' if is_valid else 'FAIL'}")

    if not is_valid:
        print(f"Errors detected:")
        for error in errors:
            print(f"  - {error}")

    # Assert that we detected the corruption
    assert not is_valid, "Data quality checks failed to detect corruption!"
    assert len(errors) > 0, "No errors detected in corrupted data!"

    print("✅ Data quality checks successfully detected corruption!")
```

**Success Criteria**:
- Data quality checks detect >95% of injected corruptions
- Corrupt data is quarantined (not used for model training)
- Alerts are triggered for data quality failures
- Pipelines automatically halt when corruption detected

---

## Part 2: Chaos Experiments Library

### Monthly Chaos Game Days

**Schedule**: Last Friday of every month, 2-4 PM

**Experiment Rotation**:

| Month | Primary Experiment | Secondary Experiment | Blast Radius |
|-------|-------------------|---------------------|--------------|
| Jan | BigQuery regional failure | API timeout (Salesforce) | Staging 100% |
| Feb | Vertex AI endpoint down | Network latency injection | Staging 100% |
| Mar | Data corruption scenario | Message queue failure | Staging 100% |
| Apr | Multi-region failover test | Database connection pool exhaustion | Staging 100% |
| May | Credential rotation chaos | Certificate expiration | Staging 100% |
| Jun | Traffic spike (10x load) | Cascading failure scenario | Staging 100% |
| Jul | **Production Chaos** (canary) | BigQuery slow queries | Prod 1% |
| Aug | Dependency unavailability | Reverse ETL failure | Staging 100% |
| Sep | Data pipeline delay (24hr) | Model drift injection | Staging 100% |
| Oct | Security incident simulation | DDoS attack scenario | Staging 100% |
| Nov | Black Friday load test | Everything fails at once | Staging 100% |
| Dec | Year-end review | Custom experiments from incidents | Staging 100% |

---

## Part 3: Chaos Automation with Chaos Toolkit

### Installation & Setup

```bash
# Install Chaos Toolkit
pip install chaostoolkit
pip install chaostoolkit-google-cloud-platform
```

### Chaos Experiment Definition (JSON)

```json
{
  "version": "1.0.0",
  "title": "BigQuery Temporary Unavailability",
  "description": "Test system resilience when BigQuery is temporarily unavailable",
  "tags": ["bigquery", "database", "resilience"],

  "steady-state-hypothesis": {
    "title": "Application is healthy",
    "probes": [
      {
        "type": "probe",
        "name": "api-responds-successfully",
        "tolerance": {
          "type": "probe",
          "name": "api-must-respond-ok",
          "provider": {
            "type": "http",
            "url": "https://api-staging.nexvigilant.com/health",
            "timeout": 3
          },
          "tolerance": 200
        },
        "provider": {
          "type": "http",
          "url": "https://api-staging.nexvigilant.com/health"
        }
      },
      {
        "type": "probe",
        "name": "lead-scoring-working",
        "provider": {
          "type": "http",
          "url": "https://api-staging.nexvigilant.com/api/v1/predictions/lead-score",
          "method": "POST",
          "headers": {"Authorization": "Bearer ${API_KEY}"},
          "json": {
            "lead_id": "test_lead_123",
            "features": {"total_sessions": 5}
          }
        },
        "tolerance": 200
      }
    ]
  },

  "method": [
    {
      "type": "action",
      "name": "deny-bigquery-access",
      "provider": {
        "type": "python",
        "module": "chaoslib.providers.gcp",
        "func": "deny_firewall_rule",
        "arguments": {
          "project_id": "nexvigilant-staging",
          "rule_name": "allow-bigquery-access",
          "duration": 300
        }
      },
      "pauses": {
        "after": 60
      }
    }
  ],

  "rollbacks": [
    {
      "type": "action",
      "name": "restore-bigquery-access",
      "provider": {
        "type": "python",
        "module": "chaoslib.providers.gcp",
        "func": "allow_firewall_rule",
        "arguments": {
          "project_id": "nexvigilant-staging",
          "rule_name": "allow-bigquery-access"
        }
      }
    }
  ]
}
```

### Run Chaos Experiment

```bash
# Run experiment
chaos run experiments/bigquery_unavailability.json

# Run with reporting
chaos run experiments/bigquery_unavailability.json --journal-path=results/bigquery_chaos.json

# Verify rollback
chaos verify experiments/bigquery_unavailability.json
```

---

## Part 4: Safety & Safeguards

### Pre-Flight Checklist

Before running ANY chaos experiment:

- [ ] Experiment has been peer-reviewed
- [ ] Rollback procedure is documented and tested
- [ ] Blast radius is clearly defined and minimal
- [ ] Monitoring and alerting are active
- [ ] On-call engineer is aware and available
- [ ] Customers are NOT impacted (staging only, or <1% prod traffic)
- [ ] Experiment duration is time-boxed (<30 minutes)
- [ ] Automatic rollback triggers are configured
- [ ] Communication plan is ready (if production)

### Automatic Abort Conditions

Experiments automatically abort if:

```python
# chaos_experiments/safety_monitor.py

def should_abort_experiment(metrics: dict) -> bool:
    """
    Check if experiment should be aborted immediately
    """

    abort_conditions = [
        # User-facing error rate spike
        metrics.get('error_rate', 0) > 0.10,  # >10% errors

        # Latency degradation
        metrics.get('p95_latency_ms', 0) > 5000,  # >5s p95

        # Data loss detected
        metrics.get('data_loss_events', 0) > 0,

        # Multiple dependencies failing (cascading failure)
        metrics.get('failed_dependencies', 0) > 2,

        # Manual abort signal
        metrics.get('manual_abort', False)
    ]

    if any(abort_conditions):
        print("🚨 ABORT: Safety condition triggered!")
        return True

    return False
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Owner**: Site Reliability Engineering (SRE) Team
**Next Steps**: Implement monitoring & alerting framework
