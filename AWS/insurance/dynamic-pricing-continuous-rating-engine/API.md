# API Documentation - GTM Dynamic Pricing & Continuous Rating Engine

## Overview

The Dynamic Pricing & Continuous Rating Engine provides a RESTful API for submitting real-time pricing adjustment requests. The engine processes IoT telematics data, market signals, and behavioral insights to generate dynamic premium proposals with full audit trails and actuarial approval workflows.

## Base URL

```
Production:  https://api.pricing-engine.company.com/v1
Staging:     https://staging-api.pricing-engine.company.com/v1
Development: http://localhost:8000/v1
```

## Authentication

The API supports two authentication methods:

### API Key Authentication
```bash
curl -H "X-API-Key: your-api-key" \
  https://api.pricing-engine.company.com/v1/health
```

### Bearer Token (JWT)
```bash
curl -H "Authorization: Bearer your-jwt-token" \
  https://api.pricing-engine.company.com/v1/health
```

## Quick Start

### 1. Health Check

Verify the pricing engine is operational:

```bash
curl -X GET https://api.pricing-engine.company.com/v1/health \
  -H "X-API-Key: your-api-key"

# Response (200 OK):
{
  "status": "healthy",
  "services": {
    "dynamodb": "ok",
    "sagemaker": "ok",
    "bedrock": "ok",
    "lambda": "ok"
  },
  "timestamp": "2024-03-26T10:30:45.123Z"
}
```

### 2. Submit a Pricing Review Request

Trigger a dynamic pricing evaluation based on current signals:

```bash
curl -X POST https://api.pricing-engine.company.com/v1/pricing/simulate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "FL-992-APEX",
    "current_premium": 125000,
    "telematics_score": 72,
    "metadata": {
      "vehicle_age": 3,
      "annual_mileage": 12500,
      "driver_tenure": 8,
      "claims_count": 0
    }
  }'

# Response (202 Accepted):
{
  "proposal_id": "PROP-20240326-A1B2C3",
  "status": "simulation_in_progress",
  "policy_id": "FL-992-APEX",
  "orchestration_context": "s3://bucket/proposals/PROP-20240326-A1B2C3/context.json",
  "timestamp": "2024-03-26T10:30:45.123Z",
  "message": "Pricing simulation started - results will be available in 2-3 minutes"
}
```

### 3. Check Proposal Status

Monitor the pricing proposal workflow:

```bash
curl -X GET https://api.pricing-engine.company.com/v1/proposal/PROP-20240326-A1B2C3 \
  -H "X-API-Key: your-api-key"

# Response (200 OK):
{
  "proposal_id": "PROP-20240326-A1B2C3",
  "policy_id": "FL-992-APEX",
  "overall_status": "awaiting_approval",
  "stages": {
    "signal_detection": {
      "status": "completed",
      "timestamp": "2024-03-26T10:30:45.123Z"
    },
    "risk_quantification": {
      "status": "completed",
      "timestamp": "2024-03-26T10:31:15.456Z",
      "result": {
        "risk_score": 72,
        "confidence": 0.94
      }
    },
    "simulation": {
      "status": "completed",
      "timestamp": "2024-03-26T10:31:45.789Z",
      "proposed_premium": 137500,
      "delta_percentage": 10.0,
      "rationale": "Risk score 72 triggered calibration upward. Market position improved to 4.2%."
    },
    "actuarial_review": {
      "status": "pending",
      "escalation_required": false
    }
  },
  "proposal_summary": {
    "current_premium": 125000,
    "proposed_premium": 137500,
    "delta": 12500,
    "delta_percentage": 10.0,
    "effective_date": "2024-04-26"
  }
}
```

### 4. Get Proposal Details

Retrieve the full proposal document with detailed analysis:

```bash
curl -X GET https://api.pricing-engine.company.com/v1/proposal/PROP-20240326-A1B2C3/details \
  -H "X-API-Key: your-api-key"

# Response (200 OK):
{
  "proposal_id": "PROP-20240326-A1B2C3",
  "policy_id": "FL-992-APEX",
  "current_premium": 125000,
  "proposed_premium": 137500,
  "delta": 12500,
  "delta_percentage": 10.0,
  "risk_analysis": {
    "telematics_score": 72,
    "telematics_factors": {
      "harsh_braking_events": 2,
      "rapid_acceleration": 4,
      "speed_violations": 1,
      "night_driving_percentage": 15
    },
    "behavioral_signals": {
      "renewal_interest": "indicated",
      "claims_pattern": "clean_3_years",
      "policy_changes": ["coverage_limit_increase"]
    }
  },
  "market_analysis": {
    "market_average": 132000,
    "market_position_percentage": 4.2,
    "competitor_range": {
      "low": 120000,
      "high": 145000,
      "median": 130000
    }
  },
  "rationale": "Telematics score of 72 indicates improved driving behavior over the review period. However, recent harsh braking events and speed violations warrant a modest premium adjustment. Proposed rate maintains competitive positioning at 4.2% above market average, reflecting risk profile and underwriting guidelines.",
  "audit_trail": {
    "created_by": "bedrock_simulation_agent",
    "created_timestamp": "2024-03-26T10:31:45.789Z",
    "last_modified_timestamp": "2024-03-26T10:31:45.789Z"
  }
}
```

### 5. Approve or Reject Proposal

Submit actuarial decision for a pricing proposal:

```bash
# Approve proposal
curl -X POST https://api.pricing-engine.company.com/v1/proposal/PROP-20240326-A1B2C3/approve \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": "actuary-user-id",
    "notes": "Approved - modest increase justified by risk factors",
    "effective_date": "2024-04-26"
  }'

# Response (200 OK):
{
  "proposal_id": "PROP-20240326-A1B2C3",
  "status": "approved",
  "approval_timestamp": "2024-03-26T10:35:00.000Z",
  "next_step": "implementation_scheduled",
  "implementation_date": "2024-04-26",
  "message": "Proposal approved and scheduled for implementation"
}
```

```bash
# Reject proposal
curl -X POST https://api.pricing-engine.company.com/v1/proposal/PROP-20240326-A1B2C3/reject \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "rejected_by": "actuary-user-id",
    "reason": "REQUIRES_FURTHER_ANALYSIS",
    "notes": "Need more historical context for this account"
  }'

# Response (200 OK):
{
  "proposal_id": "PROP-20240326-A1B2C3",
  "status": "rejected",
  "rejection_timestamp": "2024-03-26T10:36:00.000Z",
  "reason": "REQUIRES_FURTHER_ANALYSIS",
  "next_step": "return_to_queue",
  "message": "Proposal rejected - case returned to queue for further analysis"
}
```

## API Endpoints

### POST /pricing/simulate
Initiate a pricing simulation based on current signals.

**Request:**
```json
{
  "policy_id": "string (required)",
  "current_premium": "number (required)",
  "telematics_score": "integer (required, 0-100)",
  "metadata": {
    "vehicle_age": "integer",
    "annual_mileage": "integer",
    "driver_tenure": "integer",
    "claims_count": "integer"
  }
}
```

**Response (202 Accepted):**
```json
{
  "proposal_id": "string",
  "status": "simulation_in_progress",
  "policy_id": "string",
  "orchestration_context": "string (S3 path)",
  "timestamp": "ISO 8601",
  "message": "string"
}
```

### GET /proposal/{proposal_id}
Get current status of a pricing proposal.

**Response (200 OK):**
```json
{
  "proposal_id": "string",
  "policy_id": "string",
  "overall_status": "string",
  "stages": {},
  "proposal_summary": {}
}
```

### GET /proposal/{proposal_id}/details
Retrieve full proposal details with analysis.

**Response (200 OK):**
```json
{
  "proposal_id": "string",
  "policy_id": "string",
  "current_premium": "number",
  "proposed_premium": "number",
  "delta": "number",
  "delta_percentage": "number",
  "risk_analysis": {},
  "market_analysis": {},
  "rationale": "string",
  "audit_trail": {}
}
```

### POST /proposal/{proposal_id}/approve
Approve a pricing proposal.

**Request:**
```json
{
  "approved_by": "string (required)",
  "notes": "string",
  "effective_date": "date (YYYY-MM-DD)"
}
```

**Response (200 OK):**
```json
{
  "proposal_id": "string",
  "status": "approved",
  "approval_timestamp": "ISO 8601",
  "next_step": "string",
  "implementation_date": "date",
  "message": "string"
}
```

### POST /proposal/{proposal_id}/reject
Reject a pricing proposal.

**Request:**
```json
{
  "rejected_by": "string (required)",
  "reason": "string (required)",
  "notes": "string"
}
```

**Response (200 OK):**
```json
{
  "proposal_id": "string",
  "status": "rejected",
  "rejection_timestamp": "ISO 8601",
  "reason": "string",
  "next_step": "string",
  "message": "string"
}
```

### GET /health
Health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "services": {
    "dynamodb": "ok",
    "sagemaker": "ok",
    "bedrock": "ok",
    "lambda": "ok"
  },
  "timestamp": "ISO 8601"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  },
  "timestamp": "ISO 8601"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PROPOSAL_NOT_FOUND` | 404 | Proposal ID does not exist |
| `INVALID_REQUEST` | 400 | Request validation failed |
| `POLICY_NOT_FOUND` | 404 | Policy ID not found in system |
| `AUTHORIZATION_ERROR` | 401 | Authentication failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

## Rate Limiting

API endpoints are rate-limited:
- 100 requests per minute (per API key)
- 10 concurrent requests
- Burst capacity: 150 requests

Responses include rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1711444245
```

## Webhooks

Register webhooks to receive real-time status updates:

```bash
curl -X POST https://api.pricing-engine.company.com/v1/webhooks \
  -H "X-API-Key: your-api-key" \
  -d '{
    "url": "https://your-system.com/webhooks/pricing",
    "events": ["proposal.created", "proposal.approved", "proposal.rejected"],
    "active": true
  }'
```

**Webhook Payload Example:**
```json
{
  "event": "proposal.approved",
  "proposal_id": "PROP-20240326-A1B2C3",
  "policy_id": "FL-992-APEX",
  "timestamp": "2024-03-26T10:35:00.000Z",
  "data": {
    "status": "approved",
    "current_premium": 125000,
    "proposed_premium": 137500
  }
}
```

## Batch Operations

### Batch Pricing Simulation

Submit multiple policies for pricing review:

```bash
curl -X POST https://api.pricing-engine.company.com/v1/pricing/batch-simulate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "policies": [
      {
        "policy_id": "FL-992-APEX",
        "current_premium": 125000,
        "telematics_score": 72
      },
      {
        "policy_id": "FL-993-BETA",
        "current_premium": 95000,
        "telematics_score": 68
      }
    ]
  }'

# Response (202 Accepted):
{
  "batch_id": "BATCH-20240326-001",
  "status": "processing",
  "policy_count": 2,
  "message": "Batch pricing simulation initiated"
}
```

## Best Practices

1. **Monitor Proposal Status** - Poll `/proposal/{proposal_id}` every 30 seconds until complete
2. **Use Webhooks** - Subscribe to events for real-time notifications instead of polling
3. **Cache Results** - Proposals are immutable; cache results to reduce API calls
4. **Handle Rate Limits** - Implement exponential backoff for rate limit responses
5. **Audit Logging** - Log all proposal decisions for compliance
6. **Error Handling** - Implement retry logic for transient failures (5xx errors)

## Support

For API support, contact: api-support@company.com
