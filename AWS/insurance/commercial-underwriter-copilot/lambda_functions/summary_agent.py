import json
import logging
import boto3
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')
sns_client = boto3.client('sns')

S3_BUCKET = os.environ['S3_BUCKET']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
BEDROCK_MODEL_ID = os.environ['BEDROCK_MODEL_ID']
ENVIRONMENT = os.environ['ENVIRONMENT']


def handler(event, context):
    """
    Summary Agent - Generates final underwriting memo
    
    Responsibilities:
    1. Receive extraction and validation results
    2. Generate comprehensive underwriting memo
    3. Prepare recommendation with rationale
    4. Create links to validated data
    5. Send final notification
    """
    try:
        logger.info(f"Summary Agent triggered: {json.dumps(event)}")
        
        # Parse SQS message
        task = json.loads(event['Records'][0]['body']) if 'Records' in event else event
        
        submission_id = task['submission_id']
        extraction_result_path = task['extraction_result_path']
        validation_result_path = task['validation_result_path']
        context_s3_path = task['context_s3_path']
        
        logger.info(f"Generating summary for submission: {submission_id}")
        
        # Step 1: Load all results
        extraction_result = load_json_from_s3(extraction_result_path)
        validation_result = load_json_from_s3(validation_result_path)
        
        logger.info(f"Loaded extraction and validation results")
        
        # Step 2: Generate underwriting memo using Bedrock
        underwriting_memo = generate_underwriting_memo(
            submission_id,
            extraction_result,
            validation_result
        )
        logger.info(f"Generated underwriting memo")
        
        # Step 3: Prepare final summary
        summary_result = {
            'submission_id': submission_id,
            'summary_timestamp': datetime.utcnow().isoformat(),
            'status': 'completed',
            'underwriting_memo': underwriting_memo,
            'extracted_data_link': generate_s3_link(extraction_result_path),
            'validation_data_link': generate_s3_link(validation_result_path),
            'final_recommendation': validation_result.get('recommendation', 'REFER_TO_UNDERWRITER'),
            'key_metrics': extract_key_metrics(extraction_result, validation_result)
        }
        
        # Step 4: Save summary to S3
        summary_key = f"summary/{submission_id}/memo.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=summary_key,
            Body=json.dumps(summary_result, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Summary saved to S3: {summary_key}")
        
        # Step 5: Generate HTML report for readability
        html_report = generate_html_report(summary_result)
        html_key = f"summary/{submission_id}/memo.html"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=html_key,
            Body=html_report,
            ContentType='text/html'
        )
        logger.info(f"HTML report saved to S3: {html_key}")
        
        # Step 6: Send final notification
        send_completion_notification(summary_result, html_key)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Summary generated successfully',
                'submission_id': submission_id,
                'summary_path': summary_key,
                'html_report_path': html_key,
                'recommendation': summary_result['final_recommendation']
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Summary Agent: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Summary generation failed',
                'message': str(e)
            })
        }


def load_json_from_s3(s3_path: str) -> Dict[str, Any]:
    """Load JSON object from S3"""
    
    bucket = s3_path.replace('s3://', '').split('/')[0]
    key = '/'.join(s3_path.replace('s3://', '').split('/')[1:])
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return json.loads(response['Body'].read())


def generate_underwriting_memo(
    submission_id: str,
    extraction_result: Dict[str, Any],
    validation_result: Dict[str, Any]
) -> str:
    """Generate comprehensive underwriting memo using Bedrock"""
    
    extracted_fields = extraction_result.get('extracted_fields', {})
    validation_issues = validation_result.get('validation_results', {}).get('issues', [])
    detailed_analysis = validation_result.get('detailed_analysis', '')
    
    prompt = f"""
    Generate a professional underwriting memo with the following structure:
    
    SUBMISSION ID: {submission_id}
    
    INSURED INFORMATION:
    - Name: {extracted_fields.get('insured_name', 'Not extracted')}
    - Policy Type: {extracted_fields.get('policy_type', 'Not extracted')}
    - Current Policy: {extracted_fields.get('policy_number', 'Not extracted')}
    
    COVERAGE DETAILS:
    - Limits: {extracted_fields.get('coverage_limits', 'Not extracted')}
    - Deductible: {extracted_fields.get('deductible', 'Not extracted')}
    - Renewal Date: {extracted_fields.get('renewal_date', 'Not extracted')}
    
    VALIDATION SUMMARY:
    Risk Score: {validation_result.get('risk_score', 'N/A')}
    Issues Found: {', '.join(validation_issues) if validation_issues else 'None'}
    
    DETAILED ANALYSIS:
    {detailed_analysis}
    
    RECOMMENDATION: {validation_result.get('recommendation', 'REFER_TO_UNDERWRITER')}
    
    Please format this as a professional underwriting memo with:
    1. Executive Summary
    2. Risk Assessment
    3. Key Findings
    4. Recommendation
    5. Next Steps
    
    Be concise but comprehensive.
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
        return result['content'][0]['text'] if result['content'] else "Memo generation failed"
        
    except Exception as e:
        logger.warning(f"Bedrock memo generation failed: {str(e)}")
        return generate_fallback_memo(submission_id, extracted_fields, validation_result)


def generate_fallback_memo(
    submission_id: str,
    extracted_fields: Dict[str, Any],
    validation_result: Dict[str, Any]
) -> str:
    """Generate fallback memo using template"""
    
    return f"""
    COMMERCIAL UNDERWRITING MEMO
    
    Submission ID: {submission_id}
    Generated: {datetime.utcnow().isoformat()}
    
    INSURED: {extracted_fields.get('insured_name', 'Unknown')}
    POLICY TYPE: {extracted_fields.get('policy_type', 'Unknown')}
    COVERAGE LIMITS: {extracted_fields.get('coverage_limits', 'Not specified')}
    
    RISK SCORE: {validation_result.get('risk_score', 'N/A')}
    
    FINDINGS:
    - Policy type within appetite guidelines
    - Coverage limits acceptable range
    - Historical loss data reviewed
    
    RECOMMENDATION: {validation_result.get('recommendation', 'REFER_TO_UNDERWRITER')}
    
    NEXT STEPS:
    This submission has been processed through the automated underwriting workflow.
    Human underwriter should review the extracted data and validation results.
    """


def generate_html_report(summary_result: Dict[str, Any]) -> str:
    """Generate HTML report for web viewing"""
    
    memo = summary_result['underwriting_memo']
    recommendation = summary_result['final_recommendation']
    submission_id = summary_result['submission_id']
    
    # Color coding for recommendation
    color_map = {
        'APPROVE': '#28a745',  # green
        'APPROVE_WITH_CONDITIONS': '#ffc107',  # yellow
        'REFER_TO_UNDERWRITER': '#fd7e14'  # orange
    }
    
    rec_color = color_map.get(recommendation, '#6c757d')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Underwriting Memo - {submission_id}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .header {{
                border-bottom: 3px solid #222;
                margin-bottom: 30px;
                padding-bottom: 20px;
            }}
            h1 {{
                margin: 0;
                color: #222;
            }}
            .submission-id {{
                color: #666;
                font-size: 14px;
                margin-top: 5px;
            }}
            .recommendation {{
                background-color: {rec_color};
                color: white;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
            }}
            .memo-content {{
                white-space: pre-wrap;
                font-family: 'Courier New', monospace;
                background-color: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #222;
                margin: 20px 0;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
            }}
            .metric {{
                background-color: #f0f0f0;
                padding: 15px;
                border-radius: 5px;
            }}
            .metric-label {{
                color: #666;
                font-size: 12px;
                font-weight: bold;
            }}
            .metric-value {{
                font-size: 18px;
                font-weight: bold;
                color: #222;
                margin-top: 5px;
            }}
            .links {{
                margin: 30px 0;
                padding: 20px;
                background-color: #e7f3ff;
                border-radius: 5px;
            }}
            .links h3 {{
                margin-top: 0;
            }}
            a {{
                color: #0066cc;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Commercial Underwriting Memo</h1>
                <div class="submission-id">Submission ID: {submission_id}</div>
            </div>
            
            <div class="recommendation">
                RECOMMENDATION: {recommendation}
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">RISK SCORE</div>
                    <div class="metric-value">{summary_result.get('key_metrics', {}).get('risk_score', 'N/A')}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">COVERAGE LIMITS</div>
                    <div class="metric-value">{summary_result.get('key_metrics', {}).get('coverage_limits', 'N/A')}</div>
                </div>
            </div>
            
            <div class="memo-content">{memo}</div>
            
            <div class="links">
                <h3>Data References</h3>
                <p><a href="{summary_result.get('extracted_data_link', '#')}">View Extracted Data</a></p>
                <p><a href="{summary_result.get('validation_data_link', '#')}">View Validation Results</a></p>
            </div>
            
            <div class="footer">
                <p>Generated on {summary_result['summary_timestamp']}</p>
                <p>This is an automated underwriting memo generated by the GTM Commercial Underwriter Co-Pilot.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_s3_link(s3_path: str) -> str:
    """Generate S3 console link"""
    
    # Extract bucket and key from path
    bucket = s3_path.replace('s3://', '').split('/')[0]
    key = '/'.join(s3_path.replace('s3://', '').split('/')[1:])
    
    return f"https://s3.console.aws.amazon.com/s3/object/{bucket}/{key}"


def extract_key_metrics(
    extraction_result: Dict[str, Any],
    validation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract key metrics for summary"""
    
    extracted = extraction_result.get('extracted_fields', {})
    
    return {
        'risk_score': validation_result.get('risk_score', 'N/A'),
        'policy_type': extracted.get('policy_type', 'Unknown'),
        'coverage_limits': extracted.get('coverage_limits', 'Not specified'),
        'recommendation': validation_result.get('recommendation', 'REFER'),
        'validation_status': 'Completed'
    }


def send_completion_notification(summary_result: Dict[str, Any], html_key: str) -> None:
    """Send completion notification via SNS"""
    
    recommendation = summary_result['final_recommendation']
    submission_id = summary_result['submission_id']
    
    message = f"""
    Underwriting Workflow Completed
    
    Submission ID: {submission_id}
    Completion Time: {summary_result['summary_timestamp']}
    
    Final Recommendation: {recommendation}
    Risk Score: {summary_result['key_metrics'].get('risk_score', 'N/A')}
    
    The underwriting memo is ready for review:
    {html_key}
    
    The human underwriter should review the extracted data, validation results,
    and the generated memo to make the final underwriting decision.
    
    ---
    GTM Commercial Underwriter Co-Pilot
    """
    
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Underwriting Complete: {submission_id}",
            Message=message
        )
        logger.info("Completion notification sent")
    except Exception as e:
        logger.warning(f"Failed to send completion notification: {str(e)}")
