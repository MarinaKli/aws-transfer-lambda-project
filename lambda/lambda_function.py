import boto3
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function triggered by EventBridge when a file is uploaded to S3.
    It decrypts files from 'raw/' and saves them to 'decrypted/'.
    """
    logger.info(f"Received full event: {json.dumps(event, indent=2)}")

    try:
        # Adjusted event structure parsing for EventBridge
        if 'detail' not in event or 'bucket' not in event['detail'] or 'object' not in event['detail']:
            logger.warning("Invalid event structure. No S3 details found.")
            return {'statusCode': 400, 'body': 'Invalid event structure'}

        bucket = event['detail']['bucket']['name']
        key = event['detail']['object']['key']

        # Check if file is in 'raw/' directory
        if not key.startswith('raw/'):
            logger.info(f"Skipping non-raw file: {key}")
            return {'statusCode': 200, 'body': 'File not in raw directory, skipping'}

        # Get file content
        logger.info(f"Processing file: {key} from bucket: {bucket}")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()

        # Mock decryption
        decrypted_content = mock_decrypt(file_content)

        # Create new key for decrypted file
        decrypted_key = key.replace('raw/', 'decrypted/')

        # Upload decrypted file
        s3_client.put_object(Bucket=bucket, Key=decrypted_key, Body=decrypted_content)
        logger.info(f"Decrypted file saved as: {decrypted_key}")

        return {'statusCode': 200, 'body': f"Successfully decrypted {key} to {decrypted_key}"}

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {'statusCode': 500, 'body': f"Error: {str(e)}"}

def mock_decrypt(content):
    """Mock decryption function."""
    return content[::-1]  # In a real scenario, implement actual decryption logic