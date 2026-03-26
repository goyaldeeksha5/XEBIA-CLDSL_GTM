# API Documentation - GTM Commercial Underwriter Co-Pilot

## Overview

The Commercial Underwriter Co-Pilot provides a RESTful API for submitting insurance documents for automatic triaging. The API orchestrates a multi-agent workflow that extracts data, validates against appetite guidelines, scores risk, and generates professional underwriting memos.

## Base URL

```
Production:  https://api.underwriter-copilot.company.com/v1
Staging:     https://staging-api.underwriter-copilot.company.com/v1
Development: http://localhost:8000/v1
```

## Authentication

The API supports two authentication methods:

### API Key Authentication
```bash
curl -H "X-API-Key: your-api-key" \
  https://api.underwriter-copilot.company.com/v1/health
```

### Bearer Token (JWT)
```bash
curl -H "Authorization: Bearer your-jwt-token" \
  https://api.underwriter-copilot.company.com/v1/health
```

## Quick Start

### 1. Health Check

Verify the API is operational:

```bash
curl -X GET https://api.underwriter-copilot.company.com/v1/health \
  -H "X-API-Key: your-api-key"

# Response (200 OK):
{
  "status": "healthy",
  "services": {
    "s3": "ok",
    "lambda": "ok",
    "bedrock": "ok",
    "sagemaker": "ok"
  },
  "timestamp": "2024-03-26T10:30:45.123Z"
}
```

### 2. Submit a Document for Triaging

Upload a PDF to S3 first, then submit it for processing:

```bash
# Step 1: Upload document to S3
aws s3 cp acme_renewal.pdf s3://gtm-underwriter-copilot-submissions-12345/submissions/

# Step 2: Submit for triaging
curl -X POST https://api.underwriter-copilot.company.com/v1/triage-submission \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "document_uri": "s3://gtm-underwriter-copilot-submissions-12345/submissions/acme_renewal.pdf",
    "insured_name": "ACME Corporation",
    "policy_number": "POL-2024-123456",
    "metadata": {
      "broker_id": "BROKER-001",
      "broker_name": "ABC Insurance Brokers",
      "priority": "high"
    }
  }'

# Response (202 Accepted):
{
  "submission_id": "SUB-20240326-A1B2C3D4",
  "status": "processing",
  "workflow_context_path": "s3://bucket/workflow/SUB-20240326-A1B2C3D4/context.json",
  "estimated_completion": "2024-03-26T10:35:45.123Z",
  "message": "Workflow initiated successfully - your submission is being processed"
}
```

### 3. Check Submission Status

Monitor the workflow progress:

```bash
curl -X GET https://api.underwriter-copilot.company.com/v1/submission/SUB-20240326-A1B2C3D4 \
  -H "X-API-Key: your-api-key"

# Response (200 OK):
{
  "submission_id": "SUB-20240326-A1B2C3D4",
  "overall_status": "validation-processing",
  "stages": {
    "orchestration": {
      "status": "completed",
      "completed_at": "2024-03-26T10:31:10.123Z",
      "output_path": "s3://bucket/workflow/SUB-20240326-A1B2C3D4/context.json"
    },
    "extraction": {
      "status": "completed",
      "completed_at": "2024-03-26T10:32:50.123Z",
      "output_path": "s3://bucket/extraction/SUB-20240326-A1B2C3D4/result.json"
    },
    "validation": {
      "status": "processing",
      "started_at": "2024-03-26T10:33:00.123Z",
      "output_path": null
    },
    "summary": {
      "status": "pending",
      "started_at": null,
      "output_path": null
    }
  },
  "progress_percentage": 60,
  "received_at": "2024-03-26T10:30:45.123Z",
  "estimated_completion": "2024-03-26T10:35:45.123Z",
  "document": {
    "name": "acme_renewal.pdf",
    "type": "pdf"
  }
}
```

### 4. Get Extraction Results

Retrieve data extracted from the document:

```bash
curl -X GET https://api.underwriter-copilot.company.com/v1/submission/SUB-20240326-A1B2C3D4/extraction \
  -H "X-API-Key: your-api-key"

# Response (200 OK):
{
  "submission_id": "SUB-20240326-A1B2C3D4",
  "extraction_timestamp": "2024-03-26T10:32:50.123Z",
  "status": "completed",
  "extracted_fields": {
    "insured_name": "ACME Corporation",
    "policy_number": "POL-2024-123456",
    "policy_type": "Commercial General Liability",
    "coverage_limits": "$1,000,000",
    "deductible": "$10,000",
    "renewal_date": "2024-06-30",
    "special_conditions": []
  },
  "historical_context": {
    "prior_losses": [
      { "year": 2023, "amount": 50000 },
      { "year": 2022, "amount": 0 }
    ],
    "loss_ratio": 0.25,
    "years_insured": 5
  },
  "confidence_scores": {
    "textract": 0.95,
    "bedrock": 0.88
  }
}
```

### 5. Get Validation Results

Retrieve risk scoring and compliance results:

```bash
curl -X GET https://api.underwriter-copilot.company.com/v1/submission/SUB-20240326-A1B2C3D4/validation \
  -H "X-API-Key: your-api-key"

# Response (200 OK):
{
  "submission_id": "SUB-20240326-A1B2C3D4",
  "validation_timestamp": "2024-03-26T10:34:30.123Z",
  "status": "completed",
  "risk_score": 42,
  "validation_results": {
    "policy_type_approved": true,
    "coverage_limits_approved": true,
    "loss_history_approved": true,
    "years_in_business_approved": true,
    "risk_score_approved": true,
    "overall_decision": "APPROVED",
    "issues": []
  },
  "recommendation": "APPROVE",
  "detailed_analysis": "ACME Corporation is a well-established business with acceptable coverage limits and minimal loss history. The submission meets all appetite requirements.",
  "flagged_issues": []
}
```

### 6. Get Final Underwriting Memo

Retrieve the generated memo (JSON or HTML):

```bash
# Get as JSON
curl -X GET https://api.underwriter-copilot.company.com/v1/submission/SUB-20240326-A1B2C3D4/memo \
  -H "X-API-Key: your-api-key"

# Get as HTML
curl -X GET https://api.underwriter-copilot.company.com/v1/submission/SUB-20240326-A1B2C3D4/memo?format=html \
  -H "X-API-Key: your-api-key" > memo.html

# Response (200 OK - JSON):
{
  "submission_id": "SUB-20240326-A1B2C3D4",
  "summary_timestamp": "2024-03-26T10:35:30.123Z",
  "status": "completed",
  "underwriting_memo": "COMMERCIAL UNDERWRITING MEMO...",
  "extracted_data_link": "https://s3.console.aws.amazon.com/.../extraction.json",
  "validation_data_link": "https://s3.console.aws.amazon.com/.../validation.json",
  "final_recommendation": "APPROVE",
  "key_metrics": {
    "risk_score": 42,
    "policy_type": "Commercial General Liability",
    "coverage_limits": "$1,000,000",
    "recommendation": "APPROVE"
  }
}
```

## Endpoints Reference

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check API and service health |

### Submission Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/triage-submission` | Submit document for triaging |
| GET | `/submission/{submission_id}` | Get submission status |
| GET | `/submission/{submission_id}/extraction` | Get extraction results |
| GET | `/submission/{submission_id}/validation` | Get validation results |
| GET | `/submission/{submission_id}/memo` | Get underwriting memo |
| GET | `/submissions` | List all submissions (with filters) |

### Guidelines Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/guidelines` | Get current appetite guidelines |
| PUT | `/guidelines` | Update appetite guidelines |

## Request/Response Examples

### Request: TriageSubmission

```json
{
  "document_uri": "s3://bucket/submissions/document.pdf",
  "insured_name": "Company Name",
  "policy_number": "POL-2024-001",
  "metadata": {
    "broker_id": "BROKER-001",
    "broker_name": "ABC Brokers",
    "submission_date": "2024-03-26T10:30:00Z",
    "priority": "high"
  },
  "requested_features": ["extraction", "validation", "memo"]
}
```

### Response: TriageSubmission (202 Accepted)

```json
{
  "submission_id": "SUB-20240326-A1B2C3D4",
  "status": "processing",
  "workflow_context_path": "s3://bucket/workflow/.../context.json",
  "estimated_completion": "2024-03-26T10:35:45.123Z",
  "message": "Workflow initiated successfully"
}
```

### Polling Pattern for Workflow Completion

```bash
#!/bin/bash
SUBMISSION_ID="SUB-20240326-A1B2C3D4"
POLL_INTERVAL=5  # seconds
MAX_POLLS=60     # 5 minutes total

for i in $(seq 1 $MAX_POLLS); do
  echo "Poll $i/$MAX_POLLS"
  
  STATUS=$(curl -s -H "X-API-Key: $API_KEY" \
    https://api.underwriter-copilot.company.com/v1/submission/$SUBMISSION_ID \
    | jq -r '.overall_status')
  
  if [ "$STATUS" == "completed" ]; then
    echo "Workflow completed!"
    break
  fi
  
  sleep $POLL_INTERVAL
done
```

## Error Handling

All errors follow this format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": { "additional": "context" },
  "timestamp": "2024-03-26T10:30:45.123Z",
  "request_id": "req-12345"
}
```

### Common Error Codes

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 400 | BadRequest | Missing required field or invalid format | Check request format |
| 401 | Unauthorized | Invalid or missing API key | Provide valid API key |
| 404 | NotFound | Submission or resource not found | Verify submission_id |
| 500 | InternalError | Server error during processing | Retry with backoff |
| 503 | ServiceUnavailable | Backend service unavailable | Retry later |

## Performance & Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Document Size | 100 MB | PDF documents only |
| Request Timeout | 30 seconds | Workflow continues async |
| Submission Retention | 30 days | After which archived to Glacier |
| Concurrent Submissions | 100 | Automatic throttling beyond |
| API Rate Limit | 1000 req/min | Per API key |

## Webhook Integration

Optional: Subscribe to completion webhooks:

```bash
curl -X POST https://api.underwriter-copilot.company.com/v1/webhooks \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-system.com/webhooks/underwriter",
    "events": ["submission.completed"],
    "secret": "webhook-secret-for-hmac"
  }'
```

Webhook payload:

```json
{
  "event": "submission.completed",
  "submission_id": "SUB-20240326-A1B2C3D4",
  "recommendation": "APPROVE",
  "risk_score": 42,
  "timestamp": "2024-03-26T10:35:30.123Z"
}
```

## SDK Examples

### Python

```python
import requests

api_key = "your-api-key"
base_url = "https://api.underwriter-copilot.company.com/v1"
headers = {"X-API-Key": api_key}

# Submit document
response = requests.post(
    f"{base_url}/triage-submission",
    headers=headers,
    json={
        "document_uri": "s3://bucket/document.pdf",
        "insured_name": "ACME Corp"
    }
)

submission_id = response.json()["submission_id"]

# Poll for completion
import time
while True:
    status = requests.get(
        f"{base_url}/submission/{submission_id}",
        headers=headers
    ).json()
    
    if status["overall_status"] == "completed":
        break
    
    time.sleep(5)

# Get memo
memo = requests.get(
    f"{base_url}/submission/{submission_id}/memo",
    headers=headers
).json()

print(memo["underwriting_memo"])
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const apiKey = 'your-api-key';
const baseURL = 'https://api.underwriter-copilot.company.com/v1';

const api = axios.create({
  baseURL,
  headers: { 'X-API-Key': apiKey }
});

// Submit document
const response = await api.post('/triage-submission', {
  document_uri: 's3://bucket/document.pdf',
  insured_name: 'ACME Corp'
});

const { submission_id } = response.data;

// Poll for completion
let status = 'processing';
while (status !== 'completed') {
  const result = await api.get(`/submission/${submission_id}`);
  status = result.data.overall_status;
  
  if (status !== 'completed') {
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

// Get memo
const memo = await api.get(`/submission/${submission_id}/memo`);
console.log(memo.data.underwriting_memo);
```

## Support

For API issues or questions:

1. Check this documentation
2. Review error messages and request IDs
3. Contact: api-support@company.com
4. Reference docs: https://docs.underwriter-copilot.company.com

---

**API Version**: 1.0.0  
**Last Updated**: March 26, 2024
