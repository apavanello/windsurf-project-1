import boto3
import json
from datetime import datetime
import uuid

# Create SQS client using LocalStack endpoint
sqs = boto3.client(
    'sqs',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Send 10 different messages
for i in range(10):
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
        QueueUrl='http://localhost:4566/000000000000/incoming-messages-queue',
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
    
    print(f"Message {i+1}/10 sent! MessageId: {response['MessageId']}")

print("\nAll 10 messages have been sent successfully!")
