# Testing & Error Framework - Quick Reference Guide

## Overview

This guide provides a comprehensive summary of all testing, error handling, and quality assurance processes for the Autonomous Marketing Engine.

---

## 📚 Testing Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[TESTING_STRATEGY.md](./TESTING_STRATEGY.md)** | Overall testing approach, data quality, ML validation | Start here - understand testing philosophy |
| **[performance/PERFORMANCE_TESTING.md](./performance/PERFORMANCE_TESTING.md)** | Load, stress, endurance testing | Before major releases, weekly automated runs |
| **[chaos-engineering/CHAOS_ENGINEERING.md](./chaos-engineering/CHAOS_ENGINEERING.md)** | Resilience testing, failure scenarios | Monthly game days, pre-production |
| **[../monitoring/alerting/ALERTING_AND_INCIDENT_RESPONSE.md](../monitoring/alerting/ALERTING_AND_INCIDENT_RESPONSE.md)** | Operational monitoring, incident response | Production operations, on-call reference |

---

## 🎯 Testing Checklist by Phase

### Phase 1: Foundation (Months 1-3)

**Data Quality Testing**:
- [ ] Schema validation tests for all raw tables
- [ ] Null rate checks (<5% for critical fields)
- [ ] Freshness checks (data <24 hours old)
- [ ] Duplicate detection
- [ ] Cross-system consistency checks

**Integration Testing**:
- [ ] Fivetran connector syncs successfully
- [ ] dbt models build without errors
- [ ] Reverse ETL syncs to Salesforce
- [ ] BigQuery query performance <3s for dashboards

**Monitoring Setup**:
- [ ] Data quality dashboard created
- [ ] Pipeline monitoring alerts configured
- [ ] Error rate tracking (<1% target)

### Phase 2: Predictive (Months 4-6)

**ML Model Testing**:
- [ ] Training data validation (volume, balance, no leakage)
- [ ] Model performance evaluation (accuracy >80%, AUC >0.85)
- [ ] Bias & fairness testing (80% rule)
- [ ] Drift detection baseline established
- [ ] Model explainability (SHAP values)

**API Testing**:
- [ ] Lead scoring endpoint returns 200 OK
- [ ] Prediction latency <100ms (p95)
- [ ] Invalid input returns 400 error
- [ ] Batch prediction handles 100+ leads

**Content Generation Testing**:
- [ ] Gemini generates valid subject lines
- [ ] Quality checks catch spam words
- [ ] Brand voice validation passes
- [ ] Approval workflow functional

### Phase 3: Autonomous (Months 7-12)

**End-to-End Journey Testing**:
- [ ] Onboarding journey completes successfully
- [ ] Churn prevention triggers correctly
- [ ] Multi-channel orchestration works
- [ ] AI decision logic accurate

**Performance Testing**:
- [ ] Load test: 100 concurrent users, <5% error rate
- [ ] Stress test: System handles 3x expected load
- [ ] Endurance test: 24-hour run, no memory leaks
- [ ] Spike test: Auto-scaling responds <2 minutes

**Chaos Engineering**:
- [ ] BigQuery failure - system uses fallback
- [ ] Vertex AI timeout - rule-based scoring activates
- [ ] API dependency failure - circuit breaker opens
- [ ] Data corruption detected and quarantined

---

## ⚡ Quick Commands Reference

### Data Quality Testing

```bash
# Run data quality tests
pytest tests/data_quality/ -v

# Run dbt tests
dbt test --select staging.customer_360

# Check data freshness
python scripts/testing/check_data_freshness.py

# Detect anomalies
python scripts/testing/detect_anomalies.py --table=raw_ga360_events
```

### ML Model Testing

```bash
# Validate training data
python scripts/testing/validate_training_data.py \
  --dataset=ml_datasets.lead_scoring_train

# Test model performance
python scripts/testing/test_model_performance.py \
  --endpoint=projects/123/locations/us-central1/endpoints/456 \
  --test-data=ml_datasets.lead_scoring_test

# Check for bias
python scripts/testing/test_model_fairness.py \
  --predictions-table=ml_predictions.lead_scoring_latest

# Detect drift
python scripts/testing/detect_model_drift.py \
  --reference-data=ml_datasets.lead_scoring_train \
  --current-data=staging.leads
```

### Integration Testing

```bash
# Run all integration tests
pytest tests/integration/ -v

# Test specific API endpoint
pytest tests/integration/test_prediction_api.py::test_lead_scoring_endpoint_success -v

# Test data pipeline
pytest tests/integration/test_data_pipelines.py -v
```

### Performance Testing

```bash
# Run load test (100 users, 30 min)
locust -f tests/performance/load_test_normal.py \
  --host=https://api-staging.nexvigilant.com \
  --users 100 --spawn-rate 10 --run-time 30m

# Run stress test (progressive load)
locust -f tests/performance/stress_test.py \
  --host=https://api-staging.nexvigilant.com \
  --users 1000 --spawn-rate 50 --run-time 1h

# Test BigQuery performance
pytest tests/performance/test_bigquery_performance.py -v
```

### Chaos Engineering

```bash
# Run BigQuery failure experiment
chaos run experiments/bigquery_failure.json

# Run Vertex AI timeout experiment
chaos run experiments/vertex_ai_timeout.json

# Run monthly chaos game day
./scripts/chaos/monthly_game_day.sh
```

---

## 🚨 Alert Response Quick Guide

### P0 - Critical (Immediate Response)

**API Complete Outage**:
1. Check Cloud Run service: `gcloud run services describe api-service`
2. View recent logs: `gcloud logging read "severity>=ERROR" --limit 50`
3. Rollback if recent deploy: `gcloud run services update-traffic api-service --to-revisions=PREVIOUS_REVISION=100`

**Data Corruption**:
1. **HALT PIPELINES** immediately
2. Quarantine corrupt data: `CREATE TABLE staging.customer_360_quarantine AS SELECT * FROM ... WHERE <corrupt_condition>`
3. Restore from snapshot: `CREATE OR REPLACE TABLE ... FOR SYSTEM_TIME AS OF ...`

### P1 - High (<15 min response)

**Model Accuracy Degradation**:
1. Run drift detection script
2. Check recent feature engineering changes
3. Rollback model if needed: `gcloud ai endpoints update --traffic-split=v1=100,v2=0`

**High API Error Rate (>10%)**:
1. Check Cloud Run logs for error patterns
2. Scale up if needed: `gcloud run services update --max-instances=100`
3. Enable circuit breaker for failing dependencies

### P2 - Medium (<1 hour response)

**Pipeline Delay**:
1. Check Fivetran connector status
2. If critical: Manual export/import
3. If non-critical: Monitor and let catch up

**Elevated Churn Prediction**:
1. Validate with SQL query
2. Alert Customer Success team
3. Investigate root cause (product issue?)

---

## 📊 Key Performance Indicators (KPIs)

### Testing Coverage Metrics

| Category | Target | Current | Status |
|----------|--------|---------|--------|
| **Code Coverage** | >80% | — | 🔄 TBD |
| **Data Quality Score** | >95% | — | 🔄 TBD |
| **Model Accuracy (Lead Scoring)** | >80% | — | 🔄 TBD |
| **API Error Rate** | <1% | — | 🔄 TBD |
| **API P95 Latency** | <100ms | — | 🔄 TBD |
| **Test Execution Time** | <10 min | — | 🔄 TBD |

### Quality Gate Pass Rates

| Gate | Target Pass Rate | Enforcement |
|------|------------------|-------------|
| Unit Tests | 100% | Blocking |
| Integration Tests | 100% | Blocking |
| Data Quality Tests | >95% | Blocking |
| Model Performance Tests | >80% accuracy | Blocking |
| Performance Tests | Meet SLAs | Blocking |
| Security Scans | 0 critical vulns | Blocking |
| Chaos Tests (Staging) | System recovers | Warning |

---

## 🔧 Troubleshooting Common Issues

### Issue: dbt tests failing

**Symptom**: `dbt test` returns failures

**Common Causes**:
1. Data quality degradation upstream
2. Schema changes in source systems
3. Null values in unexpected places

**Fix**:
```bash
# Identify which tests failed
dbt test --select staging.customer_360 --store-failures

# Inspect failed records
SELECT * FROM staging_dbt_test__audit.not_null_customer_360_email;

# Fix upstream data issue or update test threshold
```

---

### Issue: Locust load test shows high error rate

**Symptom**: >10% errors during load test

**Common Causes**:
1. Cloud Run instance limit hit
2. Database connection pool exhausted
3. External API rate limits

**Fix**:
```bash
# Increase Cloud Run instances
gcloud run services update api-service --max-instances=200

# Check connection pool
# Increase in app config: MAX_DB_CONNECTIONS=100

# Add exponential backoff for external APIs
```

---

### Issue: Chaos experiment doesn't trigger rollback

**Symptom**: System doesn't recover automatically

**Debug Steps**:
1. Check rollback logic in chaos experiment JSON
2. Verify abort conditions: `should_abort_experiment()`
3. Check if rollback was manually disabled
4. Test rollback in isolation

**Fix**:
```bash
# Manually trigger rollback
chaos verify experiments/bigquery_failure.json

# Test rollback function
python -c "from chaos_experiments.safety_monitor import trigger_rollback; trigger_rollback()"
```

---

## 📅 Testing Schedule

### Daily (Automated)
- ✅ Data quality tests (6 AM)
- ✅ Integration tests (on every commit)
- ✅ Security scans
- ✅ Model performance monitoring

### Weekly (Automated)
- ✅ Load tests (Sunday 2 AM)
- ✅ ML model validation
- ✅ Performance regression tests

### Monthly (Manual + Automated)
- ✅ Chaos game day (last Friday, 2-4 PM)
- ✅ Security audit
- ✅ Comprehensive performance review
- ✅ Model retraining and evaluation

### Quarterly (Manual)
- ✅ Architecture review
- ✅ Disaster recovery drill
- ✅ Compliance audit (GDPR, CCPA)
- ✅ Testing framework review and update

---

## 🎓 Best Practices

### Do's ✅

- **Test Early, Test Often**: Integrate testing into development workflow
- **Automate Everything**: Manual testing doesn't scale
- **Monitor in Production**: Testing isn't done after deployment
- **Embrace Failure**: Use chaos engineering to find weaknesses
- **Document Runbooks**: Future you will thank you
- **Blameless Postmortems**: Focus on learning, not blaming

### Don'ts ❌

- **Don't Skip Tests**: "We'll add tests later" never happens
- **Don't Test Only Happy Paths**: Most bugs live in edge cases
- **Don't Ignore Flaky Tests**: They indicate real issues
- **Don't Test in Production First**: Use staging environment
- **Don't Forget Load Testing**: Performance issues appear at scale
- **Don't Neglect Data Quality**: "Garbage in, garbage out"

---

## 🚀 Getting Started with Testing

### Week 1: Setup

1. Clone repository and install dependencies:
   ```bash
   git clone https://github.com/nexvigilant/marketing-engine.git
   cd marketing-engine
   pip install -r requirements-dev.txt
   ```

2. Configure test environments:
   ```bash
   cp .env.example .env.test
   # Edit .env.test with staging credentials
   ```

3. Run your first tests:
   ```bash
   pytest tests/ -v
   ```

### Week 2: Data Quality

1. Set up Great Expectations:
   ```bash
   great_expectations init
   great_expectations datasource new
   ```

2. Create first expectation suite:
   ```bash
   great_expectations suite new
   ```

3. Run data quality tests:
   ```bash
   great_expectations checkpoint run customer_360_checkpoint
   ```

### Week 3: Performance

1. Install Locust:
   ```bash
   pip install locust
   ```

2. Run first load test:
   ```bash
   locust -f tests/performance/load_test_normal.py --host=https://api-staging.nexvigilant.com
   ```

3. Review results and optimize

### Week 4: Chaos

1. Install Chaos Toolkit:
   ```bash
   pip install chaostoolkit chaostoolkit-google-cloud-platform
   ```

2. Run first chaos experiment (staging only!):
   ```bash
   chaos run experiments/bigquery_failure.json
   ```

3. Review results and improve resilience

---

## 📞 Support & Resources

### Internal Resources
- **Testing Strategy**: [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)
- **Runbooks**: [../monitoring/alerting/ALERTING_AND_INCIDENT_RESPONSE.md](../monitoring/alerting/ALERTING_AND_INCIDENT_RESPONSE.md)
- **Slack Channel**: `#eng-testing`
- **On-Call**: PagerDuty rotation

### External Resources
- **Great Expectations Docs**: https://docs.greatexpectations.io/
- **Locust Docs**: https://docs.locust.io/
- **Chaos Toolkit Docs**: https://chaostoolkit.org/
- **Google Cloud Testing**: https://cloud.google.com/architecture/devops/devops-tech-test-automation

---

## ✅ Testing Checklist (Pre-Production)

Before deploying to production, ensure all items are checked:

### Data Infrastructure
- [ ] All data quality tests passing (>95% pass rate)
- [ ] Data freshness SLA met (<24 hours)
- [ ] Schema validation automated
- [ ] Anomaly detection configured
- [ ] Backup and recovery tested

### ML Models
- [ ] Training data validated (no leakage, sufficient volume, balanced)
- [ ] Model accuracy meets threshold (>80%)
- [ ] Bias testing completed (80% rule)
- [ ] Drift detection configured
- [ ] Model explainability documented (SHAP values)
- [ ] Fallback logic implemented and tested

### API & Integration
- [ ] All integration tests passing
- [ ] API endpoints tested (happy path + errors)
- [ ] Latency SLA met (p95 <100ms)
- [ ] Error handling validated
- [ ] Rate limiting implemented
- [ ] Circuit breakers configured

### Performance & Load
- [ ] Load test passed (100 users, <5% error rate)
- [ ] Stress test passed (3x load handled)
- [ ] No memory leaks (24hr endurance test)
- [ ] Auto-scaling configured and tested
- [ ] Performance monitoring dashboard created

### Resilience & Chaos
- [ ] Chaos experiments run in staging
- [ ] Failover tested (BigQuery, Vertex AI)
- [ ] Circuit breakers functional
- [ ] Automatic rollback configured
- [ ] Disaster recovery plan documented

### Monitoring & Alerting
- [ ] Health check endpoint implemented
- [ ] Error tracking configured
- [ ] Performance metrics instrumented
- [ ] Alert policies created (P0-P4)
- [ ] On-call rotation established
- [ ] Runbooks documented

### Security & Compliance
- [ ] Security vulnerability scan passed
- [ ] PII data encrypted
- [ ] Access controls configured (IAM)
- [ ] Audit logging enabled
- [ ] GDPR/CCPA compliance verified

### Documentation
- [ ] README updated
- [ ] API documentation current
- [ ] Runbooks created for common issues
- [ ] Architecture diagrams updated
- [ ] Change log maintained

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Owner**: QA & DevOps Teams
**Next Review**: End of Phase 1 (Month 3)
