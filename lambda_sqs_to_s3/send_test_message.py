import boto3
import json
import os
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
AWS_ENDPOINT = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'incoming-messages-queue')
NUM_MESSAGES = int(os.getenv('NUM_MESSAGES', '10'))

# Create SQS client using LocalStack endpoint
sqs = boto3.client(
    'sqs',
    endpoint_url=AWS_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Send 10 different messages
for i in range(NUM_MESSAGES):
    # Generate unique test message
    message = {
        "test_id": f"BULK-{str(i+1).zfill(3)}",
        "message": f"Bulk test message #{i+1}",
        "timestamp": datetime.now().isoformat(),
        "uuid": str(uuid.uuid4()),
        "data": {
            "iteration": i+1,
            "type": "bulk-test",
            "priority": "high" if i < 3 else "medium" if i < 7 else "low",
            "metadata": {
                "source": "bulk-sender",
                "version": "1.0",
                "sequence": i+1
            }
        }
    }

    # Send message to SQS
    response = sqs.send_message(
        QueueUrl=f'http://localhost:4566/000000000000/{QUEUE_NAME}',
        MessageBody=json.dumps(message),
        MessageAttributes={
            'Priority': {
                'DataType': 'String',
                'StringValue': 'high' if i < 3 else 'medium' if i < 7 else 'low'
            },
            'BatchId': {
                'DataType': 'String',
                'StringValue': datetime.now().strftime("%Y%m%d_%H%M%S")
            },
            'MessageType': {
                'DataType': 'String',
                'StringValue': 'BulkTest'
            }
        }
    )
    
    logger.info(f"Message {i+1}/{NUM_MESSAGES} sent! MessageId: {response['MessageId']}")

logger.info("\nAll messages have been sent successfully!")
