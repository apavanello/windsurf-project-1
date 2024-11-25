#!/bin/bash

# Function to check if LocalStack is ready
wait_for_localstack() {
    echo "Waiting for LocalStack to be ready..."
    while ! curl -s http://localhost:4566/_localstack/health | grep -q '"running": true'; do
        sleep 2
    done
    echo "LocalStack is ready!"
}

# Start LocalStack and other services
start_services() {
    echo "Starting services..."
    docker-compose up -d
    wait_for_localstack
}

# Initialize Terraform
init_terraform() {
    echo "Initializing Terraform..."
    docker-compose run --rm terraform init
    docker-compose run --rm terraform apply -auto-approve
}

# Create test resources
create_test_resources() {
    echo "Creating test resources..."
    # Create S3 bucket
    aws --endpoint-url=http://localhost:4566 s3 mb s3://sqs-messages-bucket

    # Create SQS queue
    aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name incoming-messages-queue
}

# Send test messages
send_messages() {
    echo "Sending test messages..."
    docker-compose run --rm message-sender
}

# Clean up resources
cleanup() {
    echo "Cleaning up resources..."
    docker-compose down -v
    rm -rf volume/
}

# Main script
case "$1" in
    "start")
        start_services
        init_terraform
        ;;
    "stop")
        cleanup
        ;;
    "restart")
        cleanup
        start_services
        init_terraform
        ;;
    "init")
        init_terraform
        ;;
    "test-resources")
        create_test_resources
        ;;
    "send-messages")
        send_messages
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|init|test-resources|send-messages}"
        exit 1
        ;;
esac

exit 0
