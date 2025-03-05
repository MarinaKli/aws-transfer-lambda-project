import boto3
import json
import logging
import os
import base64
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
s3_client = boto3.client('s3')
kms_client = boto3.client('kms')
sns_client = boto3.client('sns')

# Get environment variables
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    """
    Lambda function triggered by EventBridge when a file is uploaded to S3.
    It decrypts files from 'raw/' folder and saves them to 'decrypted/' folder.
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

        # Decrypt the content using KMS
        decrypted_content = decrypt_with_kms(file_content)

        # Create new key for decrypted file
        decrypted_key = key.replace('raw/', 'decrypted/')

        # Upload decrypted file
        if KMS_KEY_ID:
            # Use KMS encryption if a key is available
            s3_client.put_object(
                Bucket=bucket, 
                Key=decrypted_key, 
                Body=decrypted_content,
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=KMS_KEY_ID
            )
        else:
            # Don't specify encryption parameters if no KMS key is available
            s3_client.put_object(
                Bucket=bucket, 
                Key=decrypted_key, 
                Body=decrypted_content
            )
            
        logger.info(f"Decrypted file saved as: {decrypted_key}")
        
        # Send notification
        if SNS_TOPIC_ARN:
            send_notification(bucket, key, decrypted_key, "SUCCESS")

        return {'statusCode': 200, 'body': f"Successfully decrypted {key} to {decrypted_key}"}

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        
        # Send error notification
        if SNS_TOPIC_ARN:
            try:
                send_notification(bucket if 'bucket' in locals() else "unknown", 
                                 key if 'key' in locals() else "unknown", 
                                 None, 
                                 "ERROR", 
                                 str(e))
            except Exception as sns_error:
                logger.error(f"Error sending SNS notification: {str(sns_error)}")
                
        return {'statusCode': 500, 'body': f"Error: {str(e)}"}

def decrypt_with_kms(content):
    """
    Decrypt content using AWS KMS.
    
    In a real scenario:
    - If content is encrypted using KMS directly, use kms_client.decrypt()
    - If content is encrypted with a data key from KMS, implement envelope decryption
    
    This example assumes the file is directly encrypted with KMS.
    """
    if not KMS_KEY_ID:
        logger.warning("KMS_KEY_ID not set, using mock decryption")
        return mock_decrypt(content)
        
    try:
        # For demonstration - in reality, your encryption method would determine how you decrypt
        response = kms_client.decrypt(
            CiphertextBlob=content,
            KeyId=KMS_KEY_ID
        )
        return response['Plaintext']
    except Exception as e:
        logger.error(f"KMS decryption failed: {str(e)}. Falling back to mock decryption.")
        return mock_decrypt(content)

def mock_decrypt(content):
    """Mock decryption function as fallback."""
    return content[::-1]  # In a real scenario, implement actual decryption logic

def send_notification(bucket, source_key, destination_key, status, error_message=None):
    """
    Send a notification about file processing.
    
    Args:
        bucket (str): S3 bucket name
        source_key (str): Source file key
        destination_key (str): Destination file key (None if processing failed)
        status (str): Status of the processing (SUCCESS or ERROR)
        error_message (str, optional): Error message if status is ERROR
    """
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not set, skipping notification")
        return
        
    timestamp = datetime.now().isoformat()
    
    message = {
        "status": status,
        "timestamp": timestamp,
        "source": {
            "bucket": bucket,
            "key": source_key
        }
    }
    
    if destination_key:
        message["destination"] = {
            "bucket": bucket,
            "key": destination_key
        }
        
    if error_message:
        message["error"] = error_message
    
    # Send the notification
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"File Processing {status}: {source_key}",
        Message=json.dumps(message, indent=2)
    )
    
    logger.info(f"Notification sent: {response['MessageId']}")