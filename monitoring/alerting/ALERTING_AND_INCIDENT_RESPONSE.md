# Alerting & Incident Response Playbooks
## Autonomous Marketing Engine Operations

## Overview

This document defines the alerting strategy, incident response procedures, and operational runbooks for the Autonomous Marketing Engine. The goal is to detect issues before they impact customers and respond swiftly when incidents occur.

---

## Alert Severity Levels

| Severity | Description | Response Time | Escalation | Examples |
|----------|-------------|---------------|------------|----------|
| **P0 - Critical** | Complete system outage or data loss | Immediate (24/7) | Page on-call immediately | API completely down, data corruption detected, security breach |
| **P1 - High** | Major functionality degraded, significant customer impact | <15 minutes | Page on-call during business hours | 50% error rate, model predictions failing, key integration down |
| **P2 - Medium** | Partial degradation, workaround available | <1 hour | Slack alert to team | 10% error rate, high latency, non-critical pipeline delayed |
| **P3 - Low** | Minor issue, no customer impact | <4 hours | Ticket created | Data quality warning, low disk space warning, non-production issue |
| **P4 - Info** | Informational, no action required | N/A | Log only | Successful deployments, batch job completions, metrics thresholds |

---

## Part 1: Alert Definitions

### Critical Alerts (P0)

#### Alert: API Complete Outage

**Trigger Condition**:
```sql
-- Cloud Monitoring Alert Policy
-- Trigger: API health check fails for 2 consecutive minutes

SELECT
  COUNTIF(status_code != 200) / COUNT(*) as error_rate
FROM `monitoring.api_health_checks`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 MINUTE)
  AND endpoint = '/health'
HAVING error_rate >= 1.0  -- 100% failure
```

**Alert Configuration**:
```yaml
alert_policy:
  display_name: "API Complete Outage"
  severity: CRITICAL
  conditions:
    - display_name: "Health check failure"
      condition_threshold:
        filter: |
          resource.type="cloud_run_revision"
          metric.type="run.googleapis.com/request_count"
          metric.label.response_code_class="5xx"
        comparison: COMPARISON_GT
        threshold_value: 0.99
        duration: 120s
  notification_channels:
    - pagerduty_critical
    - slack_critical
    - sms_oncall
  documentation:
    content: |
      API is completely down. Follow runbook:
      https://docs.nexvigilant.com/runbooks/api-outage
```

**Incident Response Runbook**:

1. **Immediate Actions (0-5 minutes)**
   - [ ] Acknowledge alert in PagerDuty
   - [ ] Join incident channel: `#incident-api-outage`
   - [ ] Check Cloud Run service status: `gcloud run services list --platform managed`
   - [ ] Check recent deployments: Last deployment timestamp
   - [ ] Declare incident: `!incident declare API Complete Outage`

2. **Investigation (5-15 minutes)**
   - [ ] Check Cloud Logging for errors:
     ```bash
     gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit 50 --format json
     ```
   - [ ] Check database connectivity: BigQuery, Vertex AI endpoints
   - [ ] Check external dependencies: Salesforce, Braze status pages
   - [ ] Review recent config changes: Firewall rules, IAM permissions

3. **Mitigation (15-30 minutes)**
   - [ ] If recent deployment: **Rollback immediately**
     ```bash
     gcloud run services update-traffic api-service --to-revisions=PREVIOUS_REVISION=100
     ```
   - [ ] If database issue: Switch to read-only mode, use cached data
   - [ ] If dependency issue: Enable circuit breaker, use fallback data
   - [ ] Communicate status to stakeholders via status page

4. **Recovery Verification (30-45 minutes)**
   - [ ] Verify health check returns 200 OK
   - [ ] Test critical user flows (lead scoring, customer 360)
   - [ ] Monitor error rate returns to <1%
   - [ ] Gradual traffic ramp if using canary deployment

5. **Post-Incident (Within 24 hours)**
   - [ ] Write incident report (5 Whys analysis)
   - [ ] Identify root cause
   - [ ] Create action items to prevent recurrence
   - [ ] Update runbook based on learnings
   - [ ] Conduct blameless postmortem meeting

---

#### Alert: Data Corruption Detected

**Trigger Condition**:
```sql
-- Data quality check fails
SELECT
  COUNT(*) as corrupt_records
FROM `staging.customer_360`
WHERE DATE(_processed_timestamp) = CURRENT_DATE()
  AND (
    email IS NULL
    OR customer_id IS NULL
    OR email NOT LIKE '%@%'
    OR predicted_clv < 0
  )
HAVING corrupt_records > 100  -- >100 corrupt records
```

**Incident Response Runbook**:

1. **Immediate Actions (0-5 minutes)**
   - [ ] **HALT ALL PIPELINES** - Stop data ingestion immediately
     ```bash
     # Pause Fivetran connectors
     curl -X PATCH https://api.fivetran.com/v1/connectors/{connector_id} \
       -H "Authorization: Bearer $FIVETRAN_API_KEY" \
       -d '{"paused": true}'
     ```
   - [ ] Quarantine corrupt data:
     ```sql
     CREATE TABLE `staging.customer_360_quarantine` AS
     SELECT * FROM `staging.customer_360`
     WHERE <corruption_conditions>;

     DELETE FROM `staging.customer_360`
     WHERE <corruption_conditions>;
     ```
   - [ ] Notify data team and stakeholders

2. **Investigation (5-30 minutes)**
   - [ ] Identify source of corruption (which pipeline/connector?)
   - [ ] Check data lineage: Where did corrupt data originate?
   - [ ] Determine extent: How many records affected? How far back?
   - [ ] Check for data loss: Are there missing records?

3. **Remediation (30-120 minutes)**
   - [ ] If source system issue: Coordinate with vendor (Salesforce, etc.)
   - [ ] If transformation logic bug: Fix dbt model, reprocess
   - [ ] If infrastructure: Restore from backup/snapshot
   - [ ] Backfill clean data:
     ```sql
     -- Restore from table snapshot
     CREATE OR REPLACE TABLE `staging.customer_360` AS
     SELECT * FROM `staging.customer_360`
     FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR);
     ```

4. **Prevention**
   - [ ] Implement stricter data quality gates
   - [ ] Add schema validation pre-processing
   - [ ] Set up automated daily data quality reports

---

### High Alerts (P1)

#### Alert: Model Accuracy Degradation

**Trigger**: Model accuracy drops below 75% (threshold: 80%)

**Runbook**:

1. **Immediate** (0-15 min)
   - [ ] Check model prediction logs for errors
   - [ ] Verify model endpoint is responding
   - [ ] Compare recent predictions vs. actual outcomes

2. **Investigation** (15-60 min)
   - [ ] Run drift detection:
     ```bash
     python scripts/testing/detect_model_drift.py \
       --reference-data ml_datasets.lead_scoring_train \
       --current-data staging.leads \
       --model lead-scoring-v2
     ```
   - [ ] Check for data quality issues in input features
   - [ ] Review recent changes to feature engineering

3. **Mitigation**
   - [ ] If drift detected: Trigger model retraining
   - [ ] If data quality issue: Fix upstream pipeline
   - [ ] If no clear cause: Rollback to previous model version
     ```bash
     gcloud ai endpoints update $ENDPOINT_ID \
       --traffic-split=lead-scoring-v1=100,lead-scoring-v2=0
     ```

---

#### Alert: High API Error Rate (>10%)

**Trigger**:
```sql
SELECT
  COUNTIF(status_code >= 500) / COUNT(*) as error_rate
FROM `logs.api_requests`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
HAVING error_rate > 0.10
```

**Runbook**:

1. **Immediate**
   - [ ] Check Cloud Run service health
   - [ ] Review error logs for patterns:
     ```bash
     gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" \
       --limit 100 --format=json | jq '.[] | .jsonPayload.message'
     ```
   - [ ] Identify affected endpoints (all vs. specific)

2. **Common Causes & Fixes**

   **Cause: Database Connection Pool Exhausted**
   ```
   Error: "could not obtain connection from pool"
   Fix: Increase connection pool size or identify connection leaks
   ```

   **Cause: Vertex AI Timeout**
   ```
   Error: "Deadline exceeded calling Vertex AI"
   Fix: Increase timeout, or enable fallback logic
   ```

   **Cause: Memory Exhaustion (OOM)**
   ```
   Error: "process killed: out of memory"
   Fix: Increase Cloud Run memory limit or optimize code
   ```

   **Cause: Rate Limit Hit (External API)**
   ```
   Error: "429 Too Many Requests"
   Fix: Implement exponential backoff, request rate limit increase
   ```

3. **Mitigation**
   - [ ] Scale up Cloud Run instances: `gcloud run services update api-service --max-instances=100`
   - [ ] Enable circuit breaker for failing dependencies
   - [ ] If upstream service down: Return cached data or 503 with retry-after header

---

### Medium Alerts (P2)

#### Alert: Pipeline Delay

**Trigger**: ETL pipeline hasn't completed in expected timeframe (>2 hours delay)

**Runbook**:

1. **Check Status**
   ```bash
   # Check Fivetran connector status
   curl https://api.fivetran.com/v1/connectors/{connector_id} \
     -H "Authorization: Bearer $FIVETRAN_API_KEY"
   ```

2. **Common Issues**
   - Source system slow/unavailable: Wait and monitor
   - Schema change in source: Update connector mappings
   - BigQuery quota exceeded: Request quota increase

3. **Mitigation**
   - If critical data needed: Manual data export/import
   - If non-critical: Allow pipeline to catch up, monitor

---

#### Alert: Elevated Churn Prediction

**Trigger**: >20% of active customers flagged as high churn risk

**Runbook**:

1. **Validate Alert**
   ```sql
   SELECT
     COUNT(*) as total_customers,
     COUNTIF(churn_risk_tier = 'high') as high_risk_count,
     SAFE_DIVIDE(COUNTIF(churn_risk_tier = 'high'), COUNT(*)) as high_risk_pct
   FROM `marts.churn_predictions`
   WHERE prediction_date = CURRENT_DATE()
   ```

2. **Investigate**
   - [ ] Check for recent product issues or outages
   - [ ] Review customer feedback/support tickets
   - [ ] Verify model isn't experiencing drift
   - [ ] Check if specific customer segment is affected

3. **Action**
   - [ ] Alert Customer Success team
   - [ ] Trigger targeted retention campaigns
   - [ ] Investigate root cause (product, service, price?)

---

## Part 2: Monitoring Dashboards

### Executive SLA Dashboard (Real-Time)

**URL**: https://monitoring.nexvigilant.com/executive

**Metrics**:
```
┌────────────────────────────────────────────────────────┐
│           AUTONOMOUS MARKETING ENGINE STATUS           │
├────────────────────────────────────────────────────────┤
│                                                         │
│  System Health: ●●●●● 99.97%                          │
│  API Latency (P95): 87ms     [Target: <100ms]         │
│  Error Rate: 0.3%            [Target: <1%]            │
│  Active Users: 45,234                                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ API Requests/Minute                             │  │
│  │ ▂▃▅▇█▇▅▃▂▂▃▅▇█▇▅▃ Current: 1,250 RPM           │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Critical Services Status:                             │
│  ✅ BigQuery                        99.99%             │
│  ✅ Vertex AI                       99.95%             │
│  ✅ Cloud Run (API)                 99.98%             │
│  ⚠️  Salesforce Integration         98.2%  (Degraded) │
│  ✅ Braze (Email/Push)              99.97%             │
│                                                         │
│  Active Incidents: 0                                   │
│  Alerts (Last 24h): 3 warnings, 0 critical            │
│                                                         │
└────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
# cloud_functions/status_dashboard.py

from google.cloud import monitoring_v3, bigquery
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/status')
def get_system_status():
    """
    Fetch real-time system status for dashboard
    """

    bq_client = bigquery.Client()

    # API Health
    query = """
    SELECT
      COUNTIF(status_code = 200) / COUNT(*) as success_rate,
      APPROX_QUANTILES(latency_ms, 100)[OFFSET(95)] as p95_latency,
      COUNT(*) as total_requests
    FROM `logs.api_requests`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
    """
    api_health = bq_client.query(query).to_dataframe().iloc[0]

    # Service Health (check each dependency)
    services = {
        'bigquery': check_bigquery_health(),
        'vertex_ai': check_vertex_ai_health(),
        'cloud_run': check_cloud_run_health(),
        'salesforce': check_salesforce_health(),
        'braze': check_braze_health()
    }

    # Active Incidents
    incidents = get_active_incidents()

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'overall_health': api_health['success_rate'] * 100,
        'api': {
            'success_rate': api_health['success_rate'],
            'p95_latency_ms': api_health['p95_latency'],
            'requests_per_minute': api_health['total_requests'] / 5
        },
        'services': services,
        'incidents': incidents
    })
```

---

### Operations Dashboard (Detailed)

**Sections**:

1. **Data Pipeline Health**
   - Fivetran connector status (last sync time, rows synced)
   - dbt model run status (success/failure, duration)
   - Data quality test results
   - BigQuery storage and query costs

2. **ML Model Performance**
   - Prediction volume (requests/hour)
   - Model latency (p50, p95, p99)
   - Accuracy metrics (updated daily)
   - Drift detection scores

3. **Customer Journey Metrics**
   - Active journeys and user counts
   - Journey completion rates
   - Drop-off points
   - Email/SMS delivery rates

4. **Infrastructure Metrics**
   - Cloud Run: CPU, memory, instance count
   - BigQuery: Active queries, slots used
   - Vertex AI: Endpoint requests, errors

---

## Part 3: Incident Management Process

### Incident Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                   INCIDENT LIFECYCLE                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. DETECTION                                            │
│     └─ Automated alert fires OR human reports issue     │
│                                                          │
│  2. TRIAGE (0-5 min)                                    │
│     ├─ Assess severity (P0-P4)                          │
│     ├─ Determine customer impact                        │
│     └─ Assign incident commander                        │
│                                                          │
│  3. RESPONSE (5-60 min)                                 │
│     ├─ Form response team                               │
│     ├─ Create incident channel (#incident-YYYY-MM-DD-N) │
│     ├─ Begin investigation                              │
│     └─ Implement mitigation                             │
│                                                          │
│  4. RESOLUTION (Variable)                               │
│     ├─ Root cause identified                            │
│     ├─ Fix implemented                                  │
│     └─ Service restored                                 │
│                                                          │
│  5. POST-MORTEM (24-48 hrs)                             │
│     ├─ Write incident report                            │
│     ├─ Blameless review meeting                         │
│     ├─ Create action items                              │
│     └─ Update runbooks                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Incident Response Roles

| Role | Responsibilities | Who |
|------|------------------|-----|
| **Incident Commander** | Lead response, make decisions, coordinate team | On-call SRE/DevOps |
| **Tech Lead** | Deep technical investigation, implement fixes | Senior Engineer |
| **Communications Lead** | Update stakeholders, status page, post-mortem | Product Manager |
| **Customer Support Liaison** | Interface with support team, gather customer feedback | Support Manager |
| **Executive Sponsor** | Decision maker for major incidents (P0 only) | VP Engineering |

### Incident Communication Templates

**Internal Status Update (Every 30 minutes)**:
```
[TIME] Status Update - Incident #2025-10-23-001

Current Status: INVESTIGATING / MITIGATING / RESOLVED
Severity: P1
Impact: 15% of API requests failing for lead scoring endpoint
Customer Impact: Medium - fallback scoring active, slight accuracy degradation

Progress:
- [✅] Identified root cause: Vertex AI endpoint timeout
- [🔄] IN PROGRESS: Deploying increased timeout + circuit breaker
- [  ] TODO: Verify fix in production

Next Update: 2:30 PM
Incident Channel: #incident-2025-10-23-001
```

**Customer-Facing Status Page Update**:
```
[INVESTIGATING] Lead Scoring Service Degradation

Posted: 2:00 PM EST
Updated: 2:15 PM EST

We are currently investigating intermittent issues with our lead scoring service.
Some customers may experience delays or slightly less accurate scores. Our fallback
system is active, and all leads are still being scored.

We will provide updates every 15 minutes until resolved.

Next Update: 2:30 PM EST
```

---

## Part 4: Post-Incident Process

### Incident Report Template

```markdown
# Incident Report: [Title]

**Incident ID**: INC-2025-10-23-001
**Date**: October 23, 2025
**Duration**: 45 minutes (2:00 PM - 2:45 PM EST)
**Severity**: P1
**Incident Commander**: [Name]

## Summary
[2-3 sentence summary of what happened]

## Impact
- **Users Affected**: 15% of API requests
- **Services Impacted**: Lead scoring predictions
- **Revenue Impact**: Estimated $0 (fallback system active)
- **Customer Complaints**: 0

## Timeline (All times EST)

| Time | Event |
|------|-------|
| 1:58 PM | First latency spike detected in monitoring |
| 2:00 PM | Alert fired: "High API error rate" |
| 2:02 PM | Incident declared, team assembled |
| 2:10 PM | Root cause identified: Vertex AI endpoint timeout |
| 2:20 PM | Fix deployed: Increased timeout from 2s to 5s |
| 2:30 PM | Circuit breaker enabled for resilience |
| 2:45 PM | Service fully restored, monitoring normal |
| 3:00 PM | Incident closed |

## Root Cause (5 Whys)

1. **Why did API requests fail?**
   → Vertex AI endpoint was timing out

2. **Why was Vertex AI timing out?**
   → Endpoint was overloaded with requests during traffic spike

3. **Why did traffic spike cause overload?**
   → Auto-scaling wasn't enabled on Vertex AI endpoint

4. **Why wasn't auto-scaling enabled?**
   → Configuration was not updated after recent model deployment

5. **Why was configuration not updated?**
   → Deployment checklist didn't include Vertex AI configuration review

## What Went Well
- Alert fired within 2 minutes of issue starting
- Team assembled and incident declared quickly
- Fallback system prevented customer impact
- Clear runbook made response efficient

## What Went Wrong
- Vertex AI endpoint not configured for auto-scaling
- No pre-deployment check for endpoint capacity
- Traffic spike wasn't anticipated in load testing

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Enable auto-scaling on all Vertex AI endpoints | DevOps Team | Oct 25 | ✅ Complete |
| Update deployment checklist to include Vertex AI config | SRE Team | Oct 24 | ✅ Complete |
| Add traffic spike testing to monthly load tests | QA Team | Nov 1 | 🔄 In Progress |
| Document Vertex AI scaling limits and request quota increase | ML Team | Oct 30 | 📋 Planned |
| Create dashboard to monitor Vertex AI endpoint utilization | DevOps Team | Nov 15 | 📋 Planned |

## Lessons Learned
1. Capacity planning must include all infrastructure components, not just Cloud Run
2. Deployment checklists are critical - will add automated checks where possible
3. Fallback systems work! Investment in resilience paid off.
```

---

## Part 5: On-Call Rotation & Escalation

### On-Call Schedule

**Primary On-Call** (24/7):
- Week 1: Engineer A
- Week 2: Engineer B
- Week 3: Engineer C
- Week 4: Engineer D

**Secondary On-Call** (Backup):
- Always one engineer on backup

**Escalation Path**:
```
P0 Incident
  └─ Primary On-Call (immediate page)
      └─ If no response in 5 min → Secondary On-Call
          └─ If no response in 10 min → Engineering Manager
              └─ If no response in 15 min → VP Engineering
```

### On-Call Compensation

- **Weekday on-call**: $500/week stipend
- **Weekend on-call**: $750/week stipend
- **Incident response**: Comp time next day (1hr response = 1hr comp)
- **Major incident (>2hrs)**: Next day off

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Owner**: SRE & DevOps Team
**Review**: Quarterly + after every P0 incident
