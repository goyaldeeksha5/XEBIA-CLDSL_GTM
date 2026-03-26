import json
import logging
import boto3
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs_client = boto3.client('sqs')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
bedrock_client = boto3.client('bedrock-runtime')

EXTRACTION_QUEUE_URL = os.environ['EXTRACTION_QUEUE_URL']
VALIDATION_QUEUE_URL = os.environ['VALIDATION_QUEUE_URL']
SUMMARY_QUEUE_URL = os.environ['SUMMARY_QUEUE_URL']
S3_BUCKET = os.environ['S3_BUCKET']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
BEDROCK_MODEL_ID = os.environ['BEDROCK_MODEL_ID']
ENVIRONMENT = os.environ['ENVIRONMENT']


def handler(event, context):
    """
    Orchestration Agent - Coordinates the multi-agent workflow
    
    Flow:
    1. Receives document submission notification
    2. Creates workflow context
    3. Triggers Extraction Agent
    4. Monitors workflow progress
    5. Initiates Summary generation
    """
    try:
        logger.info(f"Orchestration Agent triggered: {json.dumps(event)}")
        
        # Parse S3 event or direct invocation
        submission_id = generate_submission_id()
        document_info = extract_document_info(event)
        
        logger.info(f"Processing submission: {submission_id}")
        
        # Create workflow context
        workflow_context = {
            'submission_id': submission_id,
            'document_s3_path': document_info['s3_path'],
            'document_name': document_info['name'],
            'file_type': document_info['file_type'],
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'initiated',
            'agent_results': {}
        }
        
        # Save workflow context to S3
        context_key = f"workflow/{submission_id}/context.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=context_key,
            Body=json.dumps(workflow_context),
            ContentType='application/json'
        )
        logger.info(f"Workflow context saved to S3: {context_key}")
        
        # Send extraction task to Extraction Agent
        extraction_task = {
            'submission_id': submission_id,
            'document_s3_path': document_info['s3_path'],
            'context_s3_path': context_key,
            'action': 'extract_data'
        }
        
        sqs_client.send_message(
            QueueUrl=EXTRACTION_QUEUE_URL,
            MessageBody=json.dumps(extraction_task)
        )
        logger.info(f"Extraction task queued for submission: {submission_id}")
        
        # Send notification
        notification_message = f"""
        New Commercial Underwriting Submission Received
        
        Submission ID: {submission_id}
        Document: {document_info['name']}
        Received: {workflow_context['timestamp']}
        Status: Processing initiated
        
        The Orchestration Agent has begun the multi-agent workflow.
        """
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"New Submission: {submission_id}",
            Message=notification_message
        )
        
        return {
            'statusCode': 202,
            'body': json.dumps({
                'message': 'Workflow initiated successfully',
                'submission_id': submission_id,
                'workflow_context_path': context_key
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Orchestration Agent: {str(e)}", exc_info=True)
        
        error_message = f"""
        Error in Commercial Underwriting Workflow
        
        Error: {str(e)}
        Time: {datetime.utcnow().isoformat()}
        Environment: {ENVIRONMENT}
        """
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Workflow Error - Orchestration Agent",
            Message=error_message
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to initiate workflow',
                'message': str(e)
            })
        }


def generate_submission_id() -> str:
    """Generate unique submission ID"""
    from uuid import uuid4
    return f"SUB-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"


def extract_document_info(event: Dict[str, Any]) -> Dict[str, str]:
    """Extract document information from event"""
    
    # Handle S3 Put event
    if 'Records' in event:
        record = event['Records'][0]
        if 's3' in record:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            return {
                's3_path': f"s3://{bucket}/{key}",
                'name': key.split('/')[-1],
                'file_type': key.split('.')[-1].lower()
            }
    
    # Handle direct invocation
    if 'document_s3_path' in event:
        path = event['document_s3_path']
        return {
            's3_path': path,
            'name': path.split('/')[-1],
            'file_type': event.get('file_type', 'pdf')
        }
    
    raise ValueError("Unable to extract document info from event")
