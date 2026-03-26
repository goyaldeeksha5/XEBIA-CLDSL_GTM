import json
import boto3
import uuid
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PROPOSAL_TABLE'])

def lambda_handler(event, context):
    # 1. Signal Detection (Stage 1)
    detail = event.get('detail', {})
    policy_id = detail.get('policy_id', 'FL-992-APEX')
    current_premium = float(detail.get('current_premium', 125000))
    risk_score = int(detail.get('telematics_score', 60))
    
    # 2. Simulation Logic (Stage 3)
    # Factor in weather risk and behavioral shifts
    risk_multiplier = 1.15 if risk_score < 65 else 1.05
    proposed_premium = current_premium * risk_multiplier
    
    # Stage 4: Competitor Benchmarking Simulation
    market_avg = 132000
    market_pos = ((proposed_premium - market_avg) / market_avg) * 100

    # 3. Create Audit Trail & Proposal (Stage 7)
    proposal_id = str(uuid.uuid4())[:8]
    proposal_data = {
        'ProposalID': proposal_id,
        'PolicyID': policy_id,
        'OriginalPremium': str(current_premium),
        'ProposedPremium': str(round(proposed_premium, 2)),
        'Rationale': f"Risk Score {risk_score} triggered calibration. Market Position: {round(market_pos, 1)}%",
        'Status': 'AWAITING_ACTUARIAL_APPROVAL'
    }
    
    table.put_item(Item=proposal_data)

    # 4. AgentCore Response Structure
    response_body = {
        "application/json": {
            "body": json.dumps(proposal_data)
        }
    }

    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup', 'GTM_Rating_Action'),
            'apiPath': event.get('apiPath', '/simulate'),
            'httpMethod': event.get('httpMethod', 'POST'),
            'httpStatusCode': 200,
            'responseBody': response_body
        }
    }
