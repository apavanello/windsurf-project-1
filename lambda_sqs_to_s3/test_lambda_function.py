import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from lambda_function import lambda_handler, process_single_message, get_s3_path

@pytest.fixture
def s3_client_mock():
    with patch('boto3.client') as mock:
        yield mock

@pytest.fixture
def lambda_context():
    context = Mock()
    context.aws_request_id = 'test-request-123'
    context.function_name = 'test-function'
    context.function_version = '$LATEST'
    return context

@pytest.fixture
def sample_event_single():
    return {
        'Records': [{
            'messageId': 'test-message-001',
            'receiptHandle': 'test-receipt-handle',
            'body': json.dumps({
                'test_id': 'TEST-001',
                'message': 'Test message content',
                'timestamp': datetime.now().isoformat()
            }),
            'messageAttributes': {
                'Priority': {
                    'stringValue': 'high',
                    'dataType': 'String'
                }
            }
        }]
    }

@pytest.fixture
def sample_event_batch():
    records = []
    for i in range(3):
        records.append({
            'messageId': f'test-message-{i+1:03d}',
            'receiptHandle': f'test-receipt-handle-{i+1}',
            'body': json.dumps({
                'test_id': f'TEST-{i+1:03d}',
                'message': f'Test message content {i+1}',
                'timestamp': datetime.now().isoformat()
            }),
            'messageAttributes': {
                'Priority': {
                    'stringValue': 'high' if i == 0 else 'medium',
                    'dataType': 'String'
                }
            }
        })
    return {'Records': records}

def test_get_s3_path():
    # Test path generation
    message_id = 'test-123'
    path = get_s3_path(message_id)
    
    # Verify path format: YYYY/MM/DD/HHMMSS_microseconds_messageId.json
    now = datetime.now()
    assert path.startswith(f"{now.year}/{now.month:02d}/{now.day:02d}/")
    assert path.endswith(f"_{message_id}.json")
    assert len(path.split('/')) == 4  # Should have 4 parts: year, month, day, filename

def test_process_single_message_success(s3_client_mock, lambda_context):
    # Arrange
    record = {
        'messageId': 'test-message-001',
        'receiptHandle': 'test-receipt-handle',
        'body': json.dumps({
            'test_data': 'test content'
        }),
        'messageAttributes': {}
    }
    bucket_name = 'test-bucket'
    
    # Act
    success, message_id = process_single_message(record, s3_client_mock, bucket_name, lambda_context)
    
    # Assert
    assert success is True
    assert message_id == 'test-message-001'
    s3_client_mock.put_object.assert_called_once()
    call_args = s3_client_mock.put_object.call_args[1]
    assert call_args['Bucket'] == bucket_name
    assert 'Body' in call_args
    assert 'Metadata' in call_args

def test_process_single_message_failure(s3_client_mock, lambda_context):
    # Arrange
    record = {
        'messageId': 'test-message-001',
        'receiptHandle': 'test-receipt-handle',
        'body': json.dumps({
            'test_data': 'test content'
        }),
        'messageAttributes': {}
    }
    s3_client_mock.put_object.side_effect = Exception('Test error')
    
    # Act
    success, message_id = process_single_message(record, s3_client_mock, 'test-bucket', lambda_context)
    
    # Assert
    assert success is False
    assert message_id == 'test-message-001'

def test_lambda_handler_single_message(s3_client_mock, lambda_context, sample_event_single):
    # Arrange
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = s3_client_mock
        
        # Act
        result = lambda_handler(sample_event_single, lambda_context)
        
        # Assert
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['processed_messages'] == 1
        assert response_body['error_count'] == 0
        assert response_body['total_messages'] == 1
        assert len(result['batchItemFailures']) == 0

def test_lambda_handler_batch_processing(s3_client_mock, lambda_context, sample_event_batch):
    # Arrange
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = s3_client_mock
        
        # Act
        result = lambda_handler(sample_event_batch, lambda_context)
        
        # Assert
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['processed_messages'] == 3
        assert response_body['error_count'] == 0
        assert response_body['total_messages'] == 3
        assert len(result['batchItemFailures']) == 0

def test_lambda_handler_partial_failure(s3_client_mock, lambda_context, sample_event_batch):
    # Arrange
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = s3_client_mock
        # Make the second message fail
        s3_client_mock.put_object.side_effect = [
            None,  # First message succeeds
            Exception('Test error'),  # Second message fails
            None   # Third message succeeds
        ]
        
        # Act
        result = lambda_handler(sample_event_batch, lambda_context)
        
        # Assert
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['processed_messages'] == 2
        assert response_body['error_count'] == 1
        assert response_body['total_messages'] == 3
        assert len(result['batchItemFailures']) == 1

def test_s3_metadata_format(s3_client_mock, lambda_context, sample_event_single):
    # Arrange
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = s3_client_mock
        
        # Act
        lambda_handler(sample_event_single, lambda_context)
        
        # Assert
        call_args = s3_client_mock.put_object.call_args[1]
        metadata = call_args['Metadata']
        
        # Check required metadata fields
        assert 'message_id' in metadata
        assert 'processing_timestamp' in metadata
        assert 'request_id' in metadata
        assert 'year' in metadata
        assert 'month' in metadata
        assert 'day' in metadata
        
        # Validate date format
        now = datetime.now()
        assert metadata['year'] == str(now.year)
        assert metadata['month'] == f"{now.month:02d}"
        assert metadata['day'] == f"{now.day:02d}"
