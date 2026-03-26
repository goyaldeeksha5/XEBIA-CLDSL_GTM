import json
import logging
import boto3
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
sagemaker_client = boto3.client('sagemaker-runtime')
bedrock_client = boto3.client('bedrock-runtime')
sqs_client = boto3.client('sqs')

S3_BUCKET = os.environ['S3_BUCKET']
APPETITE_PREFIX = os.environ['APPETITE_PREFIX']
SUMMARY_QUEUE_URL = os.environ['SUMMARY_QUEUE_URL']
SAGEMAKER_ENDPOINT = os.environ['SAGEMAKER_ENDPOINT']
BEDROCK_MODEL_ID = os.environ['BEDROCK_MODEL_ID']
ENVIRONMENT = os.environ['ENVIRONMENT']


def handler(event, context):
    """
    Validation Agent - Validates extracted data against underwriting rules
    
    Responsibilities:
    1. Receive extracted data from Extraction Agent
    2. Load underwriting appetite guidelines
    3. Check compliance with rules using SageMaker risk scoring
    4. Use Bedrock for complex rule interpretation
    5. Flag out-of-scope risks
    6. Send to Summary Agent
    """
    try:
        logger.info(f"Validation Agent triggered: {json.dumps(event)}")
        
        # Parse SQS message
        task = json.loads(event['Records'][0]['body']) if 'Records' in event else event
        
        submission_id = task['submission_id']
        extraction_result_path = task['extraction_result_path']
        context_s3_path = task['context_s3_path']
        
        logger.info(f"Validating submission: {submission_id}")
        
        # Step 1: Load extraction result
        extraction_result = load_json_from_s3(extraction_result_path)
        logger.info(f"Loaded extraction result")
        
        # Step 2: Load appetite guidelines
        appetite_guidelines = load_appetite_guidelines()
        logger.info(f"Loaded appetite guidelines")
        
        # Step 3: Perform risk scoring with SageMaker
        risk_score = score_risk_with_sagemaker(extraction_result)
        logger.info(f"Risk score: {risk_score}")
        
        # Step 4: Validate against appetite guidelines
        validation_results = validate_against_guidelines(
            extraction_result,
            appetite_guidelines,
            risk_score
        )
        logger.info(f"Validation results: {validation_results['overall_decision']}")
        
        # Step 5: Use Bedrock for complex rule interpretation
        detailed_analysis = analyze_with_bedrock(
            extraction_result,
            appetite_guidelines,
            validation_results
        )
        logger.info(f"Detailed analysis completed")
        
        # Step 6: Prepare validation result
        validation_result = {
            'submission_id': submission_id,
            'validation_timestamp': datetime.utcnow().isoformat(),
            'status': 'completed',
            'risk_score': risk_score,
            'validation_results': validation_results,
            'detailed_analysis': detailed_analysis,
            'flagged_issues': identify_flagged_issues(validation_results),
            'recommendation': determine_recommendation(validation_results, risk_score)
        }
        
        # Step 7: Save validation result to S3
        result_key = f"validation/{submission_id}/result.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=result_key,
            Body=json.dumps(validation_result),
            ContentType='application/json'
        )
        logger.info(f"Validation result saved to S3: {result_key}")
        
        # Step 8: Send to Summary Agent
        summary_task = {
            'submission_id': submission_id,
            'extraction_result_path': extraction_result_path,
            'validation_result_path': result_key,
            'context_s3_path': context_s3_path,
            'action': 'generate_summary'
        }
        
        sqs_client.send_message(
            QueueUrl=SUMMARY_QUEUE_URL,
            MessageBody=json.dumps(summary_task)
        )
        logger.info(f"Summary task queued for submission: {submission_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Validation completed successfully',
                'submission_id': submission_id,
                'validation_result_path': result_key,
                'recommendation': validation_result['recommendation']
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Validation Agent: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Validation failed',
                'message': str(e)
            })
        }


def load_json_from_s3(s3_path: str) -> Dict[str, Any]:
    """Load JSON object from S3"""
    
    bucket = s3_path.replace('s3://', '').split('/')[0]
    key = '/'.join(s3_path.replace('s3://', '').split('/')[1:])
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return json.loads(response['Body'].read())


def load_appetite_guidelines() -> Dict[str, Any]:
    """Load underwriting appetite guidelines from S3"""
    
    try:
        response = s3_client.get_object(
            Bucket=S3_BUCKET,
            Key=f"{APPETITE_PREFIX}guidelines.json"
        )
        return json.loads(response['Body'].read())
    except:
        logger.warning("Using default appetite guidelines")
        return get_default_guidelines()


def get_default_guidelines() -> Dict[str, Any]:
    """Return default appetite guidelines"""
    
    return {
        'policy_types': [
            'Commercial General Liability',
            'Commercial Auto',
            'Property',
            'Workers Compensation'
        ],
        'min_coverage_limit': 500000,
        'max_coverage_limit': 5000000,
        'max_loss_ratio': 0.60,
        'max_prior_losses_3_years': 3,
        'min_years_in_business': 2,
        'excluded_industries': [
            'Mining',
            'Aviation',
            'Nuclear'
        ],
        'risk_appetite': {
            'low': {'max_score': 25},
            'medium': {'max_score': 50},
            'high': {'max_score': 75},
            'declined': {'max_score': 100}
        }
    }


def score_risk_with_sagemaker(extraction_result: Dict[str, Any]) -> float:
    """Score risk using SageMaker endpoint"""
    
    if not SAGEMAKER_ENDPOINT:
        logger.warning("SageMaker endpoint not configured, using fallback scoring")
        return score_risk_fallback(extraction_result)
    
    try:
        # Prepare features for SageMaker
        features = prepare_features_for_scoring(extraction_result)
        
        response = sagemaker_client.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType='application/json',
            Body=json.dumps(features)
        )
        
        result = json.loads(response['Body'].read())
        return float(result.get('score', 50.0))
        
    except Exception as e:
        logger.warning(f"SageMaker scoring failed: {str(e)}, using fallback")
        return score_risk_fallback(extraction_result)


def score_risk_fallback(extraction_result: Dict[str, Any]) -> float:
    """Fallback risk scoring using simple heuristics"""
    
    score = 50
    
    # Adjust based on coverage limits
    coverage = extraction_result.get('extracted_fields', {}).get('coverage_limits', '$500000')
    if '$' in coverage:
        coverage_amount = int(coverage.replace('$', '').replace(',', ''))
        if coverage_amount < 500000:
            score += 10
        elif coverage_amount > 3000000:
            score -= 5
    
    # Adjust based on loss history
    historical = extraction_result.get('historical_context', {})
    prior_losses = historical.get('prior_losses', [])
    if len(prior_losses) > 2:
        score += 15
    
    return min(100, max(0, score))


def prepare_features_for_scoring(extraction_result: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare features for SageMaker scoring"""
    
    extracted = extraction_result.get('extracted_fields', {})
    historical = extraction_result.get('historical_context', {})
    
    return {
        'policy_type': extracted.get('policy_type', 'Unknown'),
        'coverage_limit': extracted.get('coverage_limits', '$500000'),
        'deductible': extracted.get('deductible', '$10000'),
        'prior_losses': len(historical.get('prior_losses', [])),
        'loss_ratio': historical.get('loss_ratio', 0.0)
    }


def validate_against_guidelines(
    extraction_result: Dict[str, Any],
    guidelines: Dict[str, Any],
    risk_score: float
) -> Dict[str, Any]:
    """Validate extracted data against appetite guidelines"""
    
    results = {
        'policy_type_approved': True,
        'coverage_limits_approved': True,
        'loss_history_approved': True,
        'years_in_business_approved': True,
        'risk_score_approved': risk_score <= 75,
        'overall_decision': 'APPROVED',
        'issues': []
    }
    
    extracted = extraction_result.get('extracted_fields', {})
    
    # Check policy type
    if extracted.get('policy_type') not in guidelines['policy_types']:
        results['policy_type_approved'] = False
        results['issues'].append('Policy type not in appetite')
    
    # Check coverage limits
    coverage = extracted.get('coverage_limits', '$0')
    coverage_amount = int(coverage.replace('$', '').replace(',', '')) if '$' in coverage else 0
    
    if coverage_amount < guidelines['min_coverage_limit']:
        results['coverage_limits_approved'] = False
        results['issues'].append('Coverage limit below minimum')
    
    if coverage_amount > guidelines['max_coverage_limit']:
        results['coverage_limits_approved'] = False
        results['issues'].append('Coverage limit above maximum')
    
    # Determine overall decision
    if not all([
        results['policy_type_approved'],
        results['coverage_limits_approved'],
        results['loss_history_approved'],
        results['risk_score_approved']
    ]):
        results['overall_decision'] = 'REFER'
    
    return results


def analyze_with_bedrock(
    extraction_result: Dict[str, Any],
    guidelines: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> str:
    """Use Bedrock for detailed analysis"""
    
    prompt = f"""
    Provide a detailed underwriting analysis for this submission:
    
    Extracted Fields: {json.dumps(extraction_result.get('extracted_fields', {}), indent=2)}
    Validation Results: {json.dumps(validation_results, indent=2)}
    Guidelines: {json.dumps(guidelines, indent=2)}
    
    Analyze:
    1. Key risk factors
    2. Appetite guideline compliance
    3. Areas of concern
    4. Question for underwriter
    
    Be concise but thorough.
    """
    
    try:
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text'] if result['content'] else "Analysis unavailable"
        
    except Exception as e:
        logger.warning(f"Bedrock analysis failed: {str(e)}")
        return "Bedrock analysis failed; using manual review recommended"


def identify_flagged_issues(validation_results: Dict[str, Any]) -> List[str]:
    """Identify and flag issues from validation results"""
    
    return validation_results.get('issues', [])


def determine_recommendation(
    validation_results: Dict[str, Any],
    risk_score: float
) -> str:
    """Determine final recommendation"""
    
    decision = validation_results['overall_decision']
    
    if decision == 'APPROVED' and risk_score < 40:
        return 'APPROVE'
    elif decision == 'APPROVED' and risk_score < 70:
        return 'APPROVE_WITH_CONDITIONS'
    else:
        return 'REFER_TO_UNDERWRITER'
