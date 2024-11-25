terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  access_key = "test"
  secret_key = "test"
  region     = "us-east-1"

  # LocalStack configurations
  skip_credentials_validation = true
  skip_metadata_api_check    = true
  skip_requesting_account_id = true

  endpoints {
    lambda = "http://localhost:4566"
    sqs    = "http://localhost:4566"
    s3     = "http://localhost:4566"
    iam    = "http://localhost:4566"
  }

  s3_use_path_style = true
}

# S3 bucket
resource "aws_s3_bucket" "message_store" {
  bucket = "sqs-messages-bucket"
  force_destroy = true
}

# SQS Queue
resource "aws_sqs_queue" "message_queue" {
  name = "incoming-messages-queue"
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "lambda_sqs_to_s3_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for the Lambda role
resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda_sqs_to_s3_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [aws_sqs_queue.message_queue.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.message_store.arn,
          "${aws_s3_bucket.message_store.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = ["arn:aws:logs:*:*:*"]
      }
    ]
  })
}

# Archive the Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}"
  output_path = "${path.module}/lambda_function.zip"
  excludes    = ["main.tf", "terraform.tfstate", "terraform.tfstate.backup", ".terraform", "README.md"]
}

# Lambda function
resource "aws_lambda_function" "sqs_to_s3" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "sqs-to-s3-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.message_store.id
    }
  }
}

# Lambda permission for SQS
resource "aws_lambda_permission" "sqs_permission" {
  statement_id  = "AllowSQSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sqs_to_s3.function_name
  principal     = "sqs.amazonaws.com"
  source_arn    = aws_sqs_queue.message_queue.arn
}

# Event Source Mapping (SQS -> Lambda)
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.message_queue.arn
  function_name    = aws_lambda_function.sqs_to_s3.function_name
  batch_size       = 10  # Process up to 10 messages at once
  enabled          = true
  
  scaling_config {
    maximum_concurrency = 2  # Allow up to 2 concurrent batches
  }

  function_response_types = ["ReportBatchItemFailures"]  # Enable partial batch responses
}
