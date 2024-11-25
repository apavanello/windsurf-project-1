@echo off
setlocal enabledelayedexpansion

:: Set environment variables
set AWS_ENDPOINT=http://localhost:4566
set AWS_DEFAULT_REGION=us-east-1
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test


:: Main script
if "%1"=="" goto usage
if "%1"=="start" (
    call :start_services
    call :init_terraform
    goto end
)
if "%1"=="stop" (
    call :cleanup
    goto end
)
if "%1"=="restart" (
    call :cleanup
    call :start_services
    call :init_terraform
    goto end
)
if "%1"=="init" (
    call :init_terraform
    goto end
)
if "%1"=="test-resources" (
    call :create_test_resources
    goto end
)
if "%1"=="send-messages" (
    call :send_messages
    goto end
)


:: Function to check if LocalStack is ready
:wait_for_localstack
echo Waiting for LocalStack to be ready...
:check_loop
curl -s http://localhost:4566/_localstack/health | findstr "\"version\": true" >nul
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto check_loop
)
echo LocalStack is ready!
goto :eof

:: Start services
:start_services
echo Starting services...
echo Starting services...
echo Starting services...
echo Starting services...
docker-compose up -d
call :wait_for_localstack
goto :eof

:: Initialize Terraform
:init_terraform
echo Initializing Terraform...
docker-compose run --rm terraform init
docker-compose run --rm terraform apply -auto-approve
goto :eof

:: Create test resources
:create_test_resources
echo Creating test resources...
aws --endpoint-url=%AWS_ENDPOINT% s3 mb s3://sqs-messages-bucket
aws --endpoint-url=%AWS_ENDPOINT% sqs create-queue --queue-name incoming-messages-queue
goto :eof

:: Send test messages
:send_messages
echo Sending test messages...
docker-compose run --rm message-sender
goto :eof

:: Clean up resources
:cleanup
echo Cleaning up resources...
docker-compose down -v
if exist volume\ rmdir /s /q volume
goto :eof

:usage
echo Usage: %0 {start^|stop^|restart^|init^|test-resources^|send-messages}
exit /b 1

:end
exit /b 0
