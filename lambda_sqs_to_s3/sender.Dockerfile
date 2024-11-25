FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir boto3

# Copy the message sender script
COPY send_test_message.py .

# Set default environment variables
ENV AWS_ENDPOINT_URL=http://localstack:4566 \
    AWS_DEFAULT_REGION=us-east-1 \
    SQS_QUEUE_NAME=incoming-messages-queue \
    NUM_MESSAGES=10 \
    NUM_THREADS=2

# Run the script
CMD ["python", "send_test_message.py"]
