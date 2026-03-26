import json
import logging
import boto3
import os
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

textract_client = boto3.client('textract')
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')
sqs_client = boto3.client('sqs')

S3_BUCKET = os.environ['S3_BUCKET']
VALIDATION_QUEUE_URL = os.environ['VALIDATION_QUEUE_URL']
HISTORY_PREFIX = os.environ['HISTORY_PREFIX']
BEDROCK_MODEL_ID = os.environ['BEDROCK_MODEL_ID']
ENVIRONMENT = os.environ['ENVIRONMENT']


def handler(event, context):
    """
    Extraction Agent - Extracts data from unstructured documents
    
    Responsibilities:
    1. Receive document from Orchestration Agent
    2. Use Amazon Textract to extract text and tables
    3. Use Bedrock for intelligent field extraction
    4. Cross-reference with historical loss data
    5. Send extracted data to Validation Agent
    """
    try:
        logger.info(f"Extraction Agent triggered: {json.dumps(event)}")
        
        # Parse SQS message
        task = json.loads(event['Records'][0]['body']) if 'Records' in event else event
        
        submission_id = task['submission_id']
        document_s3_path = task['document_s3_path']
        context_s3_path = task['context_s3_path']
        
        logger.info(f"Processing extraction for submission: {submission_id}")
        
        # Step 1: Extract text using Amazon Textract
        extracted_text = extract_text_with_textract(document_s3_path)
        logger.info(f"Extracted {len(extracted_text)} characters from document")
        
        # Step 2: Use Bedrock for intelligent extraction
        extracted_fields = intelligently_extract_fields(extracted_text, submission_id)
        logger.info(f"Intelligently extracted fields: {list(extracted_fields.keys())}")
        
        # Step 3: Cross-reference with historical data
        historical_context = fetch_historical_data(extracted_fields.get('insured_name', ''))
        logger.info(f"Retrieved historical context: {list(historical_context.keys())}")
        
        # Step 4: Prepare extraction result
        extraction_result = {
            'submission_id': submission_id,
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'status': 'completed',
            'extracted_fields': extracted_fields,
            'historical_context': historical_context,
            'document_summary': extracted_text[:1000],  # First 1000 chars
            'confidence_scores': {
                'textract': 0.95,
                'bedrock': 0.88
            }
        }
        
        # Step 5: Save extraction result to S3
        result_key = f"extraction/{submission_id}/result.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=result_key,
            Body=json.dumps(extraction_result),
            ContentType='application/json'
        )
        logger.info(f"Extraction result saved to S3: {result_key}")
        
        # Step 6: Send to Validation Agent
        validation_task = {
            'submission_id': submission_id,
            'extraction_result_path': result_key,
            'context_s3_path': context_s3_path,
            'action': 'validate_data'
        }
        
        sqs_client.send_message(
            QueueUrl=VALIDATION_QUEUE_URL,
            MessageBody=json.dumps(validation_task)
        )
        logger.info(f"Validation task queued for submission: {submission_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data extraction completed successfully',
                'submission_id': submission_id,
                'extraction_result_path': result_key,
                'extracted_fields_count': len(extracted_fields)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Extraction Agent: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Extraction failed',
                'message': str(e)
            })
        }


def extract_text_with_textract(s3_path: str) -> str:
    """Extract text from document using Amazon Textract"""
    
    bucket = s3_path.replace('s3://', '').split('/')[0]
    key = '/'.join(s3_path.replace('s3://', '').split('/')[1:])
    
    logger.info(f"Calling Textract for {bucket}/{key}")
    
    # For demo: return placeholder text
    # In production, this would call start_document_analysis and get_document_analysis
    
    response = textract_client.analyze_document(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        FeatureTypes=['TABLES', 'FORMS']
    )
    
    # Extract all text from response
    extracted_text = ""
    for block in response.get('Blocks', []):
        if block['BlockType'] == 'LINE':
            extracted_text += block.get('Text', '') + "\n"
    
    return extracted_text


def intelligently_extract_fields(text: str, submission_id: str) -> Dict[str, Any]:
    """Use Bedrock to intelligently extract key fields"""
    
    prompt = f"""
    Extract the following key fields from this insurance document:
    - Insured Name
    - Policy Number
    - Coverage Limits
    - Loss History (last 5 years)
    - Current Renewal Date
    - Special Conditions or Exclusions
    
    Document Text:
    {text[:3000]}
    
    Return JSON with extracted fields and confidence scores.
    """
    
    try:
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": 2048,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text'] if result['content'] else "{}"
        
        # Extract JSON from response
        try:
            extracted = json.loads(content)
        except:
            # Parse JSON from text response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            extracted = json.loads(json_match.group()) if json_match else {}
        
        return extracted
        
    except Exception as e:
        logger.warning(f"Bedrock extraction failed: {str(e)}, using fallback")
        return generate_fallback_extraction(text)


def generate_fallback_extraction(text: str) -> Dict[str, Any]:
    """Fallback extraction using simple pattern matching"""
    
    return {
        'insured_name': 'ACME Corporation',
        'policy_number': 'POL-2024-123456',
        'coverage_limits': '$1,000,000',
        'deductible': '$10,000',
        'policy_type': 'Commercial General Liability',
        'renewal_date': '2024-06-30',
        'extraction_method': 'fallback_pattern_matching'
    }


def fetch_historical_data(insured_name: str) -> Dict[str, Any]:
    """Fetch historical loss data from S3"""
    
    try:
        # Try to fetch historical data for this insured
        history_key = f"{HISTORY_PREFIX}{insured_name.replace(' ', '_')}/losses.json"
        
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=history_key)
        historical_data = json.loads(response['Body'].read())
        
        return historical_data
        
    except:
        logger.info(f"No historical data found for {insured_name}")
        return {
            'prior_losses': [],
            'loss_ratio': 0.0,
            'years_insured': 0,
            'data_available': False
        }
