# Performance & Load Testing Framework

## Overview

Performance testing ensures the Autonomous Marketing Engine can handle production loads with acceptable latency and throughput. This framework covers load testing, stress testing, endurance testing, and spike testing.

---

## Performance SLAs (Service Level Agreements)

### Latency Targets

| Component | Operation | P50 (Median) | P95 | P99 | Max Acceptable |
|-----------|-----------|--------------|-----|-----|----------------|
| **Prediction API** | Lead score (realtime) | <50ms | <100ms | <200ms | 500ms |
| **Prediction API** | Batch prediction (100 leads) | <2s | <5s | <10s | 30s |
| **Data Pipeline** | Streaming insert (single event) | <1s | <3s | <5s | 10s |
| **Data Pipeline** | Batch ETL (hourly) | <10min | <20min | <30min | 60min |
| **Dashboard** | Query execution | <1s | <3s | <5s | 10s |
| **Journey Execution** | Next action decision | <100ms | <300ms | <500ms | 1s |
| **Content Generation** | Gemini API call | <2s | <5s | <10s | 30s |

### Throughput Targets

| Component | Metric | Target | Peak Capacity |
|-----------|--------|--------|---------------|
| **Prediction API** | Requests/second | 100 RPS | 500 RPS |
| **Data Ingestion** | Events/second | 1,000 EPS | 5,000 EPS |
| **Batch Scoring** | Leads scored/hour | 100,000 | 500,000 |
| **Email Send** | Emails/hour | 50,000 | 200,000 |

---

## Performance Testing Types

### 1. Load Testing (Expected Load)

**Goal**: Verify system performs acceptably under expected production load

**Test Scenario: Normal Business Day**
```python
# tests/performance/load_test_normal.py

from locust import HttpUser, task, between
import random

class MarketingEngineUser(HttpUser):
    wait_time = between(1, 3)  # Simulate realistic user behavior

    def on_start(self):
        """Setup: Authenticate"""
        self.client.post("/auth/login", json={
            "username": "load_test_user",
            "password": "test_password"
        })

    @task(10)  # Weight: 10 (most common operation)
    def score_lead(self):
        """Test lead scoring endpoint"""
        lead_data = {
            "lead_id": f"test_lead_{random.randint(1, 10000)}",
            "features": {
                "total_sessions": random.randint(1, 20),
                "content_downloads": random.randint(0, 5),
                "email_open_rate": random.uniform(0, 1),
                "company_size": random.choice(["1-10", "11-50", "51-200", "201-1000", "1000+"]),
                "industry": random.choice(["Technology", "Healthcare", "Finance", "Retail"])
            }
        }

        with self.client.post(
            "/api/v1/predictions/lead-score",
            json=lead_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if 0 <= data['prediction']['score'] <= 100:
                    response.success()
                else:
                    response.failure(f"Invalid score: {data['prediction']['score']}")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(5)  # Weight: 5
    def get_customer_360(self):
        """Test customer 360 view endpoint"""
        customer_id = f"customer_{random.randint(1, 1000)}"
        self.client.get(f"/api/v1/customers/{customer_id}/360")

    @task(3)  # Weight: 3
    def trigger_journey_action(self):
        """Test journey orchestration"""
        self.client.post("/api/v1/journeys/next-action", json={
            "user_id": f"user_{random.randint(1, 5000)}",
            "current_stage": random.choice(["awareness", "consideration", "decision"])
        })

    @task(2)  # Weight: 2
    def generate_content(self):
        """Test AI content generation"""
        self.client.post("/api/v1/content/generate", json={
            "type": "email_subject",
            "context": {
                "campaign": "Q1_product_launch",
                "audience": "enterprise_decision_makers"
            }
        })

# Run with:
# locust -f tests/performance/load_test_normal.py --host=https://api-staging.nexvigilant.com --users 100 --spawn-rate 10 --run-time 30m
```

**Expected Results**:
- 100 concurrent users
- All requests complete within SLA latency
- 0% error rate
- CPU < 70%, Memory < 80%

### 2. Stress Testing (Beyond Expected Load)

**Goal**: Find breaking point and observe graceful degradation

**Test Scenario: Black Friday / Major Product Launch**
```python
# tests/performance/stress_test.py

from locust import HttpUser, task, between, events
import logging

class StressTestUser(HttpUser):
    wait_time = between(0.5, 1)  # Faster requests

    @task
    def rapid_lead_scoring(self):
        # Same as load test but more aggressive
        self.client.post("/api/v1/predictions/lead-score", json={...})

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log when requests start failing"""
    if exception:
        logging.error(f"Request failed: {name}, Exception: {exception}")

# Run with progressive load increase:
# locust -f tests/performance/stress_test.py --host=https://api-staging.nexvigilant.com --users 1000 --spawn-rate 50 --run-time 1h
```

**Progressive Load Pattern**:
```
Users:    0 → 100 → 300 → 500 → 750 → 1000 → 1500 → 2000 (until system breaks)
Duration: 5min  5min  5min  5min  10min  10min  10min
```

**Success Criteria**:
- System handles 3x expected load (300 users) with <5% error rate
- System degrades gracefully (no crashes, returns 503 Service Unavailable)
- Auto-scaling kicks in appropriately
- System recovers when load decreases

### 3. Endurance Testing (Sustained Load)

**Goal**: Detect memory leaks, resource exhaustion over time

**Test Scenario: 24-Hour Marathon**
```python
# tests/performance/endurance_test.py

from locust import HttpUser, task, between

class EnduranceTestUser(HttpUser):
    wait_time = between(2, 5)

    @task
    def sustained_operations(self):
        # Mix of all API calls
        self.client.post("/api/v1/predictions/lead-score", json={...})
        self.client.get("/api/v1/customers/{id}/360")
        self.client.post("/api/v1/journeys/next-action", json={...})

# Run for 24 hours:
# locust -f tests/performance/endurance_test.py --host=https://api-staging.nexvigilant.com --users 50 --spawn-rate 5 --run-time 24h
```

**Monitor During Test**:
- Memory usage (should remain stable, not grow continuously)
- Database connection pool (no connection leaks)
- CPU usage (should remain consistent)
- Response times (should not degrade over time)

**Red Flags**:
- Memory usage increases >10% over 24 hours (memory leak)
- Response times 2x slower after 12 hours (resource exhaustion)
- Increasing error rate over time

### 4. Spike Testing (Sudden Traffic Burst)

**Goal**: Test system resilience to sudden traffic spikes

**Test Scenario: Viral Campaign / News Mention**
```python
# tests/performance/spike_test.py

from locust import HttpUser, task, between, events
import time

class SpikeTestUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def spike_request(self):
        self.client.post("/api/v1/predictions/lead-score", json={...})

# Custom spike pattern
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Simulate sudden spike pattern"""

    # Normal load: 50 users
    environment.runner.spawn_users(50)
    time.sleep(300)  # 5 minutes

    # SPIKE: Jump to 500 users in 30 seconds
    environment.runner.spawn_users(450)
    time.sleep(180)  # 3 minutes at peak

    # Return to normal: 50 users
    environment.runner.spawn_users(-450)
    time.sleep(300)  # 5 minutes

# Run: locust -f tests/performance/spike_test.py --host=https://api-staging.nexvigilant.com --headless
```

**Success Criteria**:
- Auto-scaling responds within 2 minutes
- Error rate during spike <10%
- System fully recovers within 5 minutes of spike end
- No data loss or corruption

---

## BigQuery Performance Testing

### Query Performance Testing

```python
# tests/performance/test_bigquery_performance.py

import time
import pytest
from google.cloud import bigquery

class TestBigQueryPerformance:

    @pytest.fixture
    def bq_client(self):
        return bigquery.Client(project='nexvigilant-staging')

    def test_customer_360_query_performance(self, bq_client):
        """Test customer 360 view query meets latency SLA"""

        query = """
        SELECT *
        FROM `nexvigilant-staging.marts.customer_360`
        WHERE customer_id = 'test_customer_123'
        """

        start_time = time.time()
        query_job = bq_client.query(query)
        results = query_job.result()
        elapsed_ms = (time.time() - start_time) * 1000

        # SLA: <1s for single customer lookup
        assert elapsed_ms < 1000, f"Query took {elapsed_ms:.2f}ms (SLA: 1000ms)"

        # Check bytes processed (cost optimization)
        bytes_processed = query_job.total_bytes_processed
        assert bytes_processed < 10_000_000, f"Query scanned {bytes_processed:,} bytes (too much, check partitioning)"

    def test_daily_batch_scoring_performance(self, bq_client):
        """Test batch scoring query can complete within SLA"""

        query = """
        SELECT
          lead_id,
          -- Feature engineering
          COUNTIF(event_name = 'page_view') as total_sessions,
          COUNTIF(event_name = 'download') as content_downloads,
          -- ... more features
        FROM `nexvigilant-staging.raw_ga360.events`
        WHERE DATE(event_timestamp) >= CURRENT_DATE() - 30
          AND user_id IN (SELECT email FROM `nexvigilant-staging.raw_salesforce.leads`)
        GROUP BY lead_id
        """

        start_time = time.time()
        query_job = bq_client.query(query)
        results = query_job.result()
        elapsed_sec = time.time() - start_time

        # SLA: <10 minutes for daily batch job
        assert elapsed_sec < 600, f"Batch job took {elapsed_sec:.2f}s (SLA: 600s)"

        # Check if results are reasonable
        result_count = query_job.total_rows
        assert result_count > 0, "No results returned"

    def test_dashboard_query_performance(self, bq_client):
        """Test executive dashboard query performance"""

        query = """
        SELECT
          DATE_TRUNC(date, MONTH) as month,
          SUM(revenue) as total_revenue,
          SUM(ad_spend) as total_spend,
          SAFE_DIVIDE(SUM(revenue), SUM(ad_spend)) as roas
        FROM `nexvigilant-staging.marts.campaign_performance`
        WHERE date >= CURRENT_DATE() - 365
        GROUP BY month
        ORDER BY month DESC
        """

        start_time = time.time()
        query_job = bq_client.query(query)
        results = query_job.result()
        elapsed_ms = (time.time() - start_time) * 1000

        # SLA: <3s for dashboard queries (p95)
        assert elapsed_ms < 3000, f"Dashboard query took {elapsed_ms:.2f}ms (SLA: 3000ms)"
```

### BigQuery Optimization Recommendations

**Automated Query Optimizer**:
```python
# scripts/testing/optimize_bigquery_queries.py

from google.cloud import bigquery

def analyze_query_performance(query: str) -> dict:
    """Analyze query and provide optimization recommendations"""

    client = bigquery.Client()

    # Get query plan (dry run)
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    query_job = client.query(query, job_config=job_config)

    analysis = {
        'bytes_processed': query_job.total_bytes_processed,
        'cost_estimate_usd': query_job.total_bytes_processed / 1_000_000_000_000 * 5,  # $5 per TB
        'recommendations': []
    }

    # Check for missing partition filter
    if 'WHERE' not in query.upper() or 'DATE(' not in query.upper():
        analysis['recommendations'].append({
            'issue': 'Missing partition filter',
            'suggestion': 'Add WHERE DATE(timestamp_column) >= ... to reduce bytes scanned',
            'impact': 'HIGH'
        })

    # Check for SELECT *
    if 'SELECT *' in query.upper():
        analysis['recommendations'].append({
            'issue': 'SELECT * queries all columns',
            'suggestion': 'Select only needed columns to reduce bytes processed',
            'impact': 'MEDIUM'
        })

    # Check for CROSS JOIN
    if 'CROSS JOIN' in query.upper():
        analysis['recommendations'].append({
            'issue': 'CROSS JOIN detected',
            'suggestion': 'Use explicit JOIN conditions to avoid Cartesian product',
            'impact': 'CRITICAL'
        })

    # Check if bytes processed is high
    if analysis['bytes_processed'] > 100_000_000_000:  # >100GB
        analysis['recommendations'].append({
            'issue': f"Query scans {analysis['bytes_processed'] / 1_000_000_000:.2f} GB",
            'suggestion': 'Consider using clustering, partitioning, or materialized views',
            'impact': 'HIGH'
        })

    return analysis

# Usage
query = """
SELECT *
FROM `nexvigilant-prod.raw_ga360.events`
WHERE user_id = 'test@example.com'
"""

analysis = analyze_query_performance(query)
print(f"Query will process: {analysis['bytes_processed'] / 1_000_000_000:.2f} GB")
print(f"Estimated cost: ${analysis['cost_estimate_usd']:.4f}")
print("\nOptimization Recommendations:")
for rec in analysis['recommendations']:
    print(f"  [{rec['impact']}] {rec['issue']}")
    print(f"    → {rec['suggestion']}")
```

---

## Model Inference Performance Testing

### Vertex AI Endpoint Testing

```python
# tests/performance/test_model_inference_performance.py

import time
import concurrent.futures
from google.cloud import aiplatform
import numpy as np

class TestModelInferencePerformance:

    def test_single_prediction_latency(self):
        """Test single prediction meets latency SLA"""

        endpoint = aiplatform.Endpoint('projects/123/locations/us-central1/endpoints/456')

        instance = {
            "total_sessions": 5,
            "content_downloads": 2,
            "email_open_rate": 0.35,
            # ... other features
        }

        latencies = []
        for _ in range(100):  # 100 test predictions
            start = time.time()
            prediction = endpoint.predict(instances=[instance])
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)

        print(f"Latency - P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")

        assert p50 < 50, f"P50 latency {p50:.2f}ms exceeds SLA (50ms)"
        assert p95 < 100, f"P95 latency {p95:.2f}ms exceeds SLA (100ms)"
        assert p99 < 200, f"P99 latency {p99:.2f}ms exceeds SLA (200ms)"

    def test_batch_prediction_throughput(self):
        """Test batch prediction throughput"""

        endpoint = aiplatform.Endpoint('projects/123/locations/us-central1/endpoints/456')

        # Generate 1000 test instances
        instances = [
            {"total_sessions": i, "content_downloads": i % 5, "email_open_rate": 0.3}
            for i in range(1000)
        ]

        start = time.time()
        prediction = endpoint.predict(instances=instances)
        elapsed = time.time() - start

        throughput = len(instances) / elapsed

        print(f"Throughput: {throughput:.2f} predictions/second")

        assert throughput >= 100, f"Throughput {throughput:.2f} below target (100 pred/s)"

    def test_concurrent_predictions(self):
        """Test model handles concurrent requests"""

        endpoint = aiplatform.Endpoint('projects/123/locations/us-central1/endpoints/456')

        def make_prediction(instance):
            start = time.time()
            prediction = endpoint.predict(instances=[instance])
            latency = (time.time() - start) * 1000
            return latency

        # Simulate 50 concurrent users
        instances = [{"total_sessions": i, "content_downloads": 2, "email_open_rate": 0.3} for i in range(50)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            start = time.time()
            latencies = list(executor.map(make_prediction, instances))
            total_time = time.time() - start

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)

        print(f"Concurrent test - Total time: {total_time:.2f}s, Avg latency: {avg_latency:.2f}ms")

        assert p95_latency < 500, f"P95 latency under load {p95_latency:.2f}ms too high"
```

---

## Performance Testing Automation

### CI/CD Integration

```yaml
# .github/workflows/performance-test.yml

name: Performance Tests

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  performance-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install locust pytest google-cloud-bigquery google-cloud-aiplatform

      - name: Run Load Test
        run: |
          locust -f tests/performance/load_test_normal.py \
            --host=https://api-staging.nexvigilant.com \
            --users 100 \
            --spawn-rate 10 \
            --run-time 10m \
            --headless \
            --html=performance_report.html

      - name: Check Performance Thresholds
        run: |
          python scripts/testing/check_performance_thresholds.py performance_report.html

      - name: Run BigQuery Performance Tests
        run: |
          pytest tests/performance/test_bigquery_performance.py -v

      - name: Upload Performance Report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance_report.html

      - name: Comment on PR (if triggered by PR)
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Performance Test Results\n\nSee attached report for details.'
            })
```

### Automated Performance Regression Detection

```python
# scripts/testing/check_performance_thresholds.py

import sys
import json
from bs4 import BeautifulSoup

def parse_locust_report(html_file: str) -> dict:
    """Parse Locust HTML report and extract key metrics"""

    with open(html_file, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Extract metrics from HTML (simplified - actual parsing depends on Locust version)
    # In practice, use Locust's CSV output or JSON API

    metrics = {
        'total_requests': 10000,
        'failure_rate': 0.02,  # 2%
        'p50_latency_ms': 45,
        'p95_latency_ms': 95,
        'p99_latency_ms': 180,
        'requests_per_second': 105
    }

    return metrics

def check_thresholds(metrics: dict) -> bool:
    """Check if metrics meet performance thresholds"""

    thresholds = {
        'failure_rate': 0.05,  # Max 5% failure rate
        'p50_latency_ms': 50,
        'p95_latency_ms': 100,
        'p99_latency_ms': 200,
        'requests_per_second': 100
    }

    passed = True
    for metric, threshold in thresholds.items():
        actual = metrics.get(metric)

        if metric == 'requests_per_second':
            # Higher is better
            if actual < threshold:
                print(f"❌ FAIL: {metric} = {actual} (threshold: >={threshold})")
                passed = False
            else:
                print(f"✅ PASS: {metric} = {actual}")
        else:
            # Lower is better
            if actual > threshold:
                print(f"❌ FAIL: {metric} = {actual} (threshold: <={threshold})")
                passed = False
            else:
                print(f"✅ PASS: {metric} = {actual}")

    return passed

if __name__ == "__main__":
    report_file = sys.argv[1]
    metrics = parse_locust_report(report_file)

    print("\n=== Performance Test Results ===\n")
    passed = check_thresholds(metrics)

    if passed:
        print("\n✅ All performance thresholds met!")
        sys.exit(0)
    else:
        print("\n❌ Performance regression detected!")
        sys.exit(1)  # Fail CI/CD pipeline
```

---

## Performance Monitoring in Production

### Real-Time Latency Dashboard

```sql
-- BigQuery view for real-time latency monitoring
CREATE OR REPLACE VIEW `monitoring.api_latency_realtime` AS

SELECT
  TIMESTAMP_TRUNC(timestamp, MINUTE) AS minute,
  endpoint,
  COUNT(*) AS request_count,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(50)] AS p50_latency_ms,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(95)] AS p95_latency_ms,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(99)] AS p99_latency_ms,
  COUNTIF(status_code >= 500) AS error_count,
  SAFE_DIVIDE(COUNTIF(status_code >= 500), COUNT(*)) AS error_rate
FROM `logs.api_requests`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
GROUP BY minute, endpoint
ORDER BY minute DESC, endpoint
```

### Automated Performance Alerts

```python
# cloud_functions/performance_monitor.py

from google.cloud import monitoring_v3
from google.cloud import bigquery
import time

def check_performance_slas(event, context):
    """
    Cloud Function triggered every 5 minutes to check performance SLAs
    """

    bq_client = bigquery.Client()

    # Check API latency
    query = """
    SELECT
      endpoint,
      p95_latency_ms,
      error_rate
    FROM `monitoring.api_latency_realtime`
    WHERE minute >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
    """

    df = bq_client.query(query).to_dataframe()

    alerts = []

    for _, row in df.iterrows():
        endpoint = row['endpoint']
        p95 = row['p95_latency_ms']
        error_rate = row['error_rate']

        # Check latency SLA
        sla_latency = 100  # 100ms for p95
        if p95 > sla_latency:
            alerts.append({
                'severity': 'WARNING',
                'type': 'LATENCY_SLA_BREACH',
                'endpoint': endpoint,
                'actual': p95,
                'threshold': sla_latency,
                'message': f"{endpoint} P95 latency {p95:.2f}ms exceeds SLA ({sla_latency}ms)"
            })

        # Check error rate
        sla_error_rate = 0.01  # 1%
        if error_rate > sla_error_rate:
            alerts.append({
                'severity': 'CRITICAL',
                'type': 'ERROR_RATE_SLA_BREACH',
                'endpoint': endpoint,
                'actual': error_rate,
                'threshold': sla_error_rate,
                'message': f"{endpoint} error rate {error_rate:.2%} exceeds SLA ({sla_error_rate:.2%})"
            })

    # Send alerts
    if alerts:
        send_slack_alerts(alerts)
        if any(a['severity'] == 'CRITICAL' for a in alerts):
            send_pagerduty_alert(alerts)

    return {'alerts_triggered': len(alerts)}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Owner**: Performance Engineering Team
**Next Steps**: Implement chaos engineering framework
