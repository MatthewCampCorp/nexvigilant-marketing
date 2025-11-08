# BigQuery Authentication Setup

## Overview

The Data Intelligence Agent requires Google Cloud authentication to access BigQuery. This is a **one-time setup** required before running integration tests or production deployments.

## Status

- ✅ **Unit Tests**: All coordinator and data intelligence unit tests pass without authentication
- ⏳ **Integration Tests**: 7 tests require BigQuery authentication (expected)
- 📝 **Authentication Required**: Before running integration tests or production use

## Setup Steps

### 1. Authenticate with Google Cloud

Run the following command to authenticate:

```bash
gcloud auth application-default login
```

This will:
- Open your browser for OAuth authentication
- Store credentials in `~/.config/gcloud/application_default_credentials.json`
- Enable all Google Cloud SDK tools to access your GCP resources

### 2. Verify Authentication

Check your authentication status:

```bash
gcloud auth application-default print-access-token
```

If this returns an access token (starting with `ya29.`), authentication is successful.

### 3. Set Project Context

Ensure your project is set correctly:

```bash
gcloud config set project nexvigilant-digital-clubhouse
```

### 4. Verify BigQuery Access

Test BigQuery connectivity:

```bash
bq ls
```

This should list your BigQuery datasets without errors.

### 5. Re-run Integration Tests

Once authenticated, re-run the data intelligence tests:

```bash
cd C:\Users\campi\nexvigilant-marketing\agents
./venv/Scripts/python.exe -m pytest data_intelligence/tests/ -v
```

All 18 tests should now pass ✅

## Test Results Summary

### Without Authentication
- **Coordinator Tests**: 18/18 passed ✅
- **Data Intelligence Unit Tests**: 11/18 passed ✅
- **Data Intelligence Integration Tests**: 7/18 failed (authentication required) ⏳

### With Authentication (Expected)
- **All Tests**: 36/36 passed ✅

## Integration Tests Requiring Authentication

The following test methods require BigQuery authentication:

1. `test_analyze_customer_segments_structure` - Queries `customer_360` table
2. `test_analyze_customers_structure` - Analyzes customer data
3. `test_analyze_campaign_performance_structure` - Queries campaign metrics
4. Additional integration tests in `TestDataIntelligenceIntegration` class

## Troubleshooting

### Error: "Reauthentication is needed"

**Cause**: Credentials have expired or are not present

**Solution**: Run `gcloud auth application-default login` again

### Error: "Permission denied on BigQuery"

**Cause**: Your GCP account lacks BigQuery permissions

**Solution**: Grant yourself the `roles/bigquery.user` role:
```bash
gcloud projects add-iam-policy-binding nexvigilant-digital-clubhouse \
  --member=user:YOUR_EMAIL@domain.com \
  --role=roles/bigquery.user
```

### Error: "Dataset not found"

**Cause**: BigQuery datasets haven't been created yet

**Solution**: Create datasets using the setup scripts in `phase-1-foundation/bigquery-schemas/`:
```bash
cd C:\Users\campi\nexvigilant-marketing\phase-1-foundation\bigquery-schemas
# Run DDL scripts to create datasets and tables
```

## Production Deployment

For production deployment to Cloud Run, use **Workload Identity** instead of user credentials:

```yaml
# In deployment/cloud-run-service.yaml
serviceAccount: marketing-agents@nexvigilant-digital-clubhouse.iam.gserviceaccount.com
```

This service account should have:
- `roles/bigquery.dataViewer` - Read access to BigQuery datasets
- `roles/bigquery.jobUser` - Execute BigQuery jobs

## Security Best Practices

- ✅ Never commit `application_default_credentials.json` to git
- ✅ Use service accounts for production deployments
- ✅ Apply principle of least privilege (grant only necessary permissions)
- ✅ Rotate credentials regularly
- ✅ Monitor BigQuery audit logs for unusual access patterns

## Next Steps

1. Complete authentication setup (this document)
2. Re-run full test suite to verify all 36 tests pass
3. Proceed with Phase 1 Week 3: Specialized Agents implementation
4. Deploy to Cloud Run with Workload Identity for production

---

**Documentation Version**: 1.0.0
**Last Updated**: 2025-01-08
**Related Files**:
- `agents/README.md` - Main setup guide
- `agents/PHASE1_IMPLEMENTATION_SUMMARY.md` - Implementation summary
- `agents/.env.example` - Environment configuration template
