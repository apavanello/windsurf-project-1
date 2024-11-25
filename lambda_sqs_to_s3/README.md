# SQS to S3 Lambda Function

## Overview
This AWS Lambda function processes messages from an SQS queue and stores them in an S3 bucket.

## Prerequisites
- AWS Account
- AWS Lambda
- Amazon SQS
- Amazon S3

## Setup Instructions
1. Create an S3 bucket to store the messages
2. Create an SQS queue
3. Create a Lambda function
4. Set the following environment variables:
   - `S3_BUCKET_NAME`: Name of the S3 bucket to store messages

## IAM Permissions
Ensure the Lambda execution role has the following permissions:
- `sqs:ReceiveMessage`
- `s3:PutObject`

## Deployment
1. Zip the contents of this directory
2. Upload to AWS Lambda
3. Configure the SQS trigger in the Lambda function

## Configuration
- Messages are stored in `sqs_messages/` prefix in S3
- Filename format: `YYYYMMDD_HHMMSS_microseconds_message.json`

## Customization
Modify `lambda_function.py` to add custom processing logic for your specific use case.

## LocalStack Setup
1. Install LocalStack:
   ```bash
   pip install localstack
   ```

2. Start LocalStack:
   ```bash
   localstack start
   ```

3. Initialize Terraform:
   ```bash
   terraform init
   ```

4. Apply the Terraform configuration:
   ```bash
   terraform apply
   ```

5. Test the setup:
   ```bash
   # Send a test message to SQS
   aws --endpoint-url=http://localhost:4566 sqs send-message \
       --queue-url http://localhost:4566/000000000000/incoming-messages-queue \
       --message-body '{"test": "message"}'

   # Check S3 bucket for the processed message
   aws --endpoint-url=http://localhost:4566 s3 ls s3://sqs-messages-bucket/sqs_messages/
   ```

## Requirements
- LocalStack
- Terraform >= 1.5.0
- AWS CLI
- Python 3.9
