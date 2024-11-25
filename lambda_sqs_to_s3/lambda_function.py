import json
import boto3
import os
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_s3_path(message_id):
    """
    Generate S3 path with YYYY/MM/DD folder structure
    """
    now = datetime.now()
    return f"{now.year}/{now.month:02d}/{now.day:02d}/{now.strftime('%H%M%S_%f')}_{message_id}.json"

def process_single_message(record, s3_client, bucket_name, context):
    """
    Process a single SQS message and store it in S3
    
    :param record: SQS message record
    :param s3_client: Boto3 S3 client
    :param bucket_name: Target S3 bucket name
    :param context: Lambda context
    :return: tuple (success, message_id)
    """
    try:
        # Extract message details
        message_id = record['messageId']
        receipt_handle = record['receiptHandle']
        message_attributes = record.get('messageAttributes', {})
        message_body = record['body']
        
        logger.info(f"""
=== Processing Message ===
RequestId: {context.aws_request_id}
MessageId: {message_id}
Timestamp: {datetime.now().isoformat()}
Attributes: {json.dumps(message_attributes, indent=2)}
Body: {json.dumps(message_body, indent=2)}
=======================
        """)
        
        # Generate S3 path with date-based folder structure
        s3_key = get_s3_path(message_id)
        
        # Prepare message metadata
        message_metadata = {
            'timestamp': datetime.now().isoformat(),
            'message_id': message_id,
            'receipt_handle': receipt_handle,
            'attributes': message_attributes,
            'body': message_body,
            'processing': {
                'request_id': context.aws_request_id,
                'function_name': context.function_name,
                'function_version': context.function_version
            }
        }
        
        # Upload message to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(message_metadata, indent=2),
            Metadata={
                'message_id': message_id,
                'processing_timestamp': datetime.now().isoformat(),
                'request_id': context.aws_request_id,
                'year': str(datetime.now().year),
                'month': f"{datetime.now().month:02d}",
                'day': f"{datetime.now().day:02d}"
            }
        )
        
        logger.info(f"""
=== Message Successfully Processed ===
RequestId: {context.aws_request_id}
MessageId: {message_id}
S3 Location: s3://{bucket_name}/{s3_key}
Processing Time: {datetime.now().isoformat()}
================================
        """)
        
        return True, message_id
    
    except Exception as e:
        logger.error(f"""
!!! Error Processing Message !!!
RequestId: {context.aws_request_id}
MessageId: {message_id if 'message_id' in locals() else 'UNKNOWN'}
Error Time: {datetime.now().isoformat()}
Error Type: {type(e).__name__}
Error Message: {str(e)}
Message Body: {json.dumps(message_body, indent=2) if 'message_body' in locals() else 'UNKNOWN'}
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        """)
        return False, message_id if 'message_id' in locals() else None

def lambda_handler(event, context):
    """
    Lambda function to process SQS messages in batch and store them in S3
    with date-based folder organization (YYYY/MM/DD)
    
    :param event: AWS Lambda uses this to pass in event data
    :param context: Runtime information provided by AWS Lambda
    :return: Processing result with batch item failures
    """
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # Get S3 bucket name from environment variable
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'default-bucket')
    
    logger.info(f"""
=== Starting Batch Processing ===
RequestId: {context.aws_request_id}
Function: {context.function_name}
Version: {context.function_version}
Records to Process: {len(event['Records'])}
Timestamp: {datetime.now().isoformat()}
============================
    """)
    
    failed_message_ids = []
    processed_count = 0
    error_count = 0
    
    # Process messages in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(10, len(event['Records']))) as executor:
        # Submit all tasks
        future_to_record = {
            executor.submit(process_single_message, record, s3_client, bucket_name, context): record
            for record in event['Records']
        }
        
        # Process completed tasks
        for future in as_completed(future_to_record):
            success, message_id = future.result()
            if success:
                processed_count += 1
            else:
                error_count += 1
                if message_id:
                    failed_message_ids.append({'itemIdentifier': message_id})
    
    # Log batch processing summary
    logger.info(f"""
=== Batch Processing Summary ===
RequestId: {context.aws_request_id}
Total Messages: {len(event['Records'])}
Successfully Processed: {processed_count}
Errors: {error_count}
Failed Message IDs: {json.dumps(failed_message_ids)}
Storage Pattern: YYYY/MM/DD/HHMMSS_microseconds_messageId.json
Completion Time: {datetime.now().isoformat()}
============================
    """)
    
    return {
        'batchItemFailures': failed_message_ids,
        'statusCode': 200,
        'body': json.dumps({
            'processed_messages': processed_count,
            'error_count': error_count,
            'total_messages': len(event['Records']),
            'storage_pattern': 'YYYY/MM/DD/HHMMSS_microseconds_messageId.json'
        })
    }
