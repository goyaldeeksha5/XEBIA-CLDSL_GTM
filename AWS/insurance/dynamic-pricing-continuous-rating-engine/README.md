# GTM Dynamic Pricing & Continuous Rating Engine

An intelligent agentic system designed to dynamically adjust insurance premiums in real-time based on IoT telematics data, market signals, and behavioral insights. This solution leverages AWS Bedrock for continuous risk analysis and SageMaker for predictive pricing models, enabling insurers to maintain competitive positioning while optimizing for profitability and risk exposure.

## Solution Architecture

### Real-Time Data Processing Pipeline

```
┌────────────────────────────────────────────────────────┐
│        IoT Telematics & Market Data Ingestion          │
│  (Sensors, APIs, Market Feeds, Behavioral Signals)     │
└────────────┬───────────────────────────────────────────┘
             │
        EventBridge
             │
             ▼
┌────────────────────────────────────────────────────────┐
│           Signal Detection & Aggregation               │
│     (Lambda: Normalize multi-source data streams)      │
└────────────┬───────────────────────────────────────────┘
             │
        DynamoDB Streams / SQS
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│         Risk Quantification & Simulation (Stage 3)      │
│  • SageMaker Model: Behavioral risk scoring            │
│  • Bedrock: Multi-step reasoning for edge cases        │
│  • Market benchmarking: Competitive analysis           │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│      Proposal Generation & Audit Trail (Stage 7)       │
│  • Dynamic pricing engine output                       │
│  • Full change rationale stored in DynamoDB            │
│  • HTML/JSON proposal formats                          │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│     Actuarial Review & Approval Workflow (Stage 8)      │
│  • Manual approval gates                               │
│  • Configurable threshold rules                        │
│  • SNS notification to underwriting team               │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│      Implementation & Compliance (Stage 10)             │
│  • Premium update execution                            │
│  • Policy system integration                           │
│  • Audit logging and compliance records                │
└─────────────────────────────────────────────────────────┘
```

### AWS Services Integration

| Service | Purpose | Stage |
|---------|---------|-------|
| **EventBridge** | Real-time event orchestration | 1, 2 |
| **Lambda** | Serverless compute for pipeline stages | 3, 4, 7, 8, 10 |
| **DynamoDB** | Telematics data, proposals, audit trails | 1-10 |
| **DynamoDB Streams** | Real-time data change capture | 2-3 |
| **SageMaker** | Risk scoring and predictive models | 3, 9 |
| **Amazon Bedrock** | Advanced reasoning for complex scenarios | 3, 5, 6 |
| **SQS** | Asynchronous task queue | 2, 7, 8 |
| **SNS** | Real-time notifications to stakeholders | 8, 9, 10 |
| **S3** | Proposal archives and audit trails | 7 |
| **CloudWatch** | Monitoring, logging, and alerting | All Stages |

## Pricing Engine Workflow

### Stage 1: Signal Detection
- IoT sensors transmit telematics data (driver behavior, vehicle diagnostics, location)
- Market data feeds consumed (competitor pricing, inflation indices, loss ratios)
- Behavioral signals captured (policy changes, claims patterns, underwriting events)
- EventBridge routes signals to Lambda for categorization

### Stage 2: Data Aggregation & Enrichment
- Normalize multi-source signals into unified format
- Cross-reference with historical policy data
- Enrich with contextual information (geography, industry, ratings)
- Store normalized data in DynamoDB for real-time querying

### Stage 3: Risk Quantification & Simulation
- SageMaker model scores ongoing behavioral/telematics risk (probabilistic)
- Bedrock performs multi-step reasoning:
  - Interprets risk scores in business context
  - Identifies emerging risk patterns
  - Simulates premium adjustments
- Competitor benchmarking analysis
- Output: Proposed premium with confidence intervals

### Stage 4-6: Market & Regulatory Analysis
- Compare proposed premium against market average
- Verify compliance with rate filing requirements
- Check appetite and underwriting guidelines
- Regulatory impact assessment

### Stage 7: Proposal Generation & Audit Trail
- Create comprehensive proposal document with:
  - Current premium, proposed premium, delta
  - Detailed rationale extracted from Bedrock reasoning
  - Risk factors and supporting metrics
  - Market position and competitive analysis
- Full audit trail stored in DynamoDB
- Proposal saved to S3 in multiple formats (JSON, HTML, PDF)

### Stage 8: Actuarial Review & Approval
- Proposals queued for human actuarial review
- SNS notifications sent to underwriting team
- Approval workflow manages:
  - Threshold-based auto-approvals (low-risk changes)
  - Manual approval for complex/high-impact changes
  - Rejection with feedback loop
- Audit trail records all decisions

### Stage 9: Market Impact Analysis (Post-Approval)
- Aggregate approved changes to monitor market movement
- Analyze competitor reactions
- Track policy renewal/lapse rates
- Feedback loop to SageMaker for model recalibration

### Stage 10: Implementation & Compliance
- Approved premiums executed in policy system
- Policy documents generated with new rates
- Customer notifications sent
- Regulatory compliance records created
- Long-term audit trail maintained

## Project Structure

```
dynamic-pricing-continuous-rating-engine/
├── provider.tf                 # AWS provider configuration
├── variables.tf                # Input variables and configuration
├── main.tf                     # Core infrastructure (DynamoDB, Lambda, EventBridge)
├── iam.tf                      # IAM roles and policies
├── outputs.tf                  # Terraform outputs
├── index.py                    # Lambda runtime code for pricing stages
├── openapi.yaml               # API specification for Bedrock/Lambda integration
├── terraform.tfvars           # Environment-specific configuration
├── lambda_function_payload.zip # Compiled Lambda deployment package
└── README.md                  # This file
```

## Key Features

### Dynamic Premium Adjustment
- Real-time risk scoring using telematics and behavioral signals
- AI-driven proposal generation with detailed rationale
- Confidence-based flagging of high-impact changes

### Actuarial Control
- Multi-stage approval workflow with human oversight
- Configurable approval thresholds
- Full audit trail of all premium changes

### Market Intelligence
- Competitor pricing benchmarking
- Market position tracking
- Renewal/lapse analysis

### Compliance & Governance
- Rate filing compliance validation
- Regulatory requirement checks
- Complete audit trails for all decisions

### Integration & Extensibility
- OpenAPI specification for easy integration
- Supports multiple data sources (IoT, APIs, feeds)
- Extensible to new pricing models

## Getting Started

### Quick Deploy (Development)
```bash
cd AWS/insurance/dynamic-pricing-continuous-rating-engine

# Build Lambda package
python3 -c "import zipfile; z = zipfile.ZipFile('lambda_function_payload.zip', 'w'); z.write('index.py')"

# Initialize and deploy
terraform init
terraform apply -auto-approve

# Capture outputs
terraform output > outputs.txt
```

### Test Pricing Simulation
```bash
# Submit test signal
aws events put-events \
  --entries file://test-signal.json \
  --region us-east-1

# Monitor execution
aws logs tail /aws/gtm/Dynamic-Pricing-Continuous-Rating-Engine --follow
```

### View Generated Proposals
```bash
# List proposals in DynamoDB
aws dynamodb scan \
  --table-name GTM_Dynamic-Pricing-Continuous-Rating-Engine_Proposals \
  --region us-east-1

# Download proposal archive from S3
aws s3 cp s3://gtm-dpcre-proposals-<account>/SUB-*/proposal.html ./proposal.html
open ./proposal.html
```

## Documentation

- **[API.md](API.md)** - RESTful API endpoints and integration guide
- **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in minutes
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment walkthrough
- **[openapi.yaml](openapi.yaml)** - OpenAPI specification

## Support & Troubleshooting

For common issues, see [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) troubleshooting section.

Contact the GTM engineering team for assistance with advanced customization or production deployment.
