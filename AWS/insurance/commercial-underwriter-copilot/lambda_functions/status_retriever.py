import json
import logging
import boto3
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

S3_BUCKET = os.environ['S3_BUCKET']


def handler(event, context):
    """
    API Gateway Status Retriever - Fetches submission status and progress
    
    Triggered by: GET /submission/{submission_id}
    
    Returns:
    - Overall workflow status
    - Individual stage status (orchestration, extraction, validation, summary)
    - Progress percentage
    - Estimated completion time
    """
    try:
        logger.info(f"Status request: {json.dumps(event)}")
        
        # Extract submission_id from path parameter
        submission_id = event['pathParameters'].get('submission_id')
        
        if not submission_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'BadRequest',
                    'message': 'Missing submission_id in path'
                })
            }
        
        logger.info(f"Retrieving status for submission: {submission_id}")
        
        # Fetch workflow context from S3
        try:
            context_key = f"workflow/{submission_id}/context.json"
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=context_key)
            workflow_context = json.loads(response['Body'].read())
        except s3_client.exceptions.NoSuchKey:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'NotFound',
                    'message': f'Submission {submission_id} not found',
                    'submission_id': submission_id
                })
            }
        
        # Build stage status information
        stages = {
            'orchestration': get_stage_status(submission_id, 'workflow'),
            'extraction': get_stage_status(submission_id, 'extraction'),
            'validation': get_stage_status(submission_id, 'validation'),
            'summary': get_stage_status(submission_id, 'summary')
        }
        
        # Calculate overall status and progress
        overall_status, progress = calculate_overall_status(stages)
        
        # Build response
        status_response = {
            'submission_id': submission_id,
            'overall_status': overall_status,
            'stages': stages,
            'progress_percentage': progress,
            'received_at': workflow_context.get('timestamp'),
            'document': {
                'name': workflow_context.get('document_name'),
                'size': workflow_context.get('document_size'),
                'type': workflow_context.get('file_type')
            }
        }
        
        # Add estimated completion if processing
        if overall_status not in ['completed', 'failed']:
            status_response['estimated_completion'] = calculate_eta(stages)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(status_response)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving status: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'InternalError',
                'message': 'Error retrieving submission status',
                'details': str(e)
            })
        }


def get_stage_status(submission_id: str, stage: str) -> Dict[str, Any]:
    """Get status information for a specific workflow stage"""
    
    try:
        # Try to fetch stage output
        output_key = f"{stage}/{submission_id}/result.json"
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=output_key)
            result = json.loads(response['Body'].read())
            
            return {
                'status': 'completed',
                'started_at': result.get('extraction_timestamp') or result.get('validation_timestamp') or result.get('summary_timestamp'),
                'completed_at': result.get('extraction_timestamp') or result.get('validation_timestamp') or result.get('summary_timestamp'),
                'output_path': f"s3://{S3_BUCKET}/{output_key}"
            }
        except s3_client.exceptions.NoSuchKey:
            pass
        
        # Try to fetch workflow context for started info
        if stage == 'extraction':
            return {
                'status': 'processing',
                'started_at': datetime.utcnow().isoformat(),
                'output_path': None
            }
        elif stage == 'validation':
            return {
                'status': 'pending',
                'started_at': None,
                'output_path': None
            }
        elif stage == 'summary':
            return {
                'status': 'pending',
                'started_at': None,
                'output_path': None
            }
        else:  # orchestration
            return {
                'status': 'completed',
                'started_at': datetime.utcnow().isoformat(),
                'output_path': f"s3://{S3_BUCKET}/workflow/{submission_id}/context.json"
            }
        
    except Exception as e:
        logger.warning(f"Error getting stage status for {stage}: {str(e)}")
        return {
            'status': 'unknown',
            'error': str(e)
        }


def calculate_overall_status(stages: Dict[str, Dict]) -> tuple:
    """Calculate overall workflow status and progress percentage"""
    
    completed_stages = 0
    total_stages = len(stages)
    
    for stage_name, stage_info in stages.items():
        status = stage_info.get('status', 'unknown')
        
        if status == 'completed':
            completed_stages += 1
    
    # Determine overall status
    has_failed = any(s.get('status') == 'failed' for s in stages.values())
    
    if has_failed:
        overall_status = 'failed'
        progress = 50
    elif completed_stages == total_stages:
        overall_status = 'completed'
        progress = 100
    elif completed_stages >= 2:
        overall_status = 'validation-processing'
        progress = 60
    elif completed_stages >= 1:
        overall_status = 'extraction-processing'
        progress = 40
    else:
        overall_status = 'initiated'
        progress = 10
    
    return overall_status, progress


def calculate_eta(stages: Dict[str, Dict]) -> str:
    """Calculate estimated time to completion"""
    
    # Simple heuristic: estimate remaining time based on stage
    # In production, use historical timing data
    
    completed_stages = sum(1 for s in stages.values() if s.get('status') == 'completed')
    
    if completed_stages == 0:
        remaining_minutes = 3  # Extraction + Validation + Summary
    elif completed_stages == 1:
        remaining_minutes = 2  # Validation + Summary
    elif completed_stages == 2:
        remaining_minutes = 1  # Summary only
    else:
        remaining_minutes = 0
    
    from datetime import timedelta
    eta = datetime.utcnow() + timedelta(minutes=remaining_minutes)
    return eta.isoformat()
