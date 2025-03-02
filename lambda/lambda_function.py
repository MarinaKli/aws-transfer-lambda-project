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
    Lambda function that processes files uploaded to an S3 bucket.
    It decrypts files from the 'raw/' prefix and saves them to the 'decrypted/' prefix.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Get the S3 bucket and object key from the event
        bucket = event['detail']['bucket']['name']
        key = event['detail']['object']['key']
        
        # Check if this is a raw file (to avoid processing already decrypted files)
        if not key.startswith('raw/'):
            logger.info(f"File {key} is not in the raw directory. Skipping.")
            return {
                'statusCode': 200,
                'body': json.dumps('File not in raw directory, skipping')
            }
        
        # Get the file content
        logger.info(f"Processing file: {key} from bucket: {bucket}")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        
        # Perform mock decryption
        decrypted_content = mock_decrypt(file_content)
        
        # Create new key for decrypted file
        decrypted_key = key.replace('raw/', 'decrypted/')
        
        # Upload decrypted file
        s3_client.put_object(
            Bucket=bucket,
            Key=decrypted_key,
            Body=decrypted_content
        )
        
        logger.info(f"Decrypted file saved as: {decrypted_key}")
        return {
            'statusCode': 200,
            'body': json.dumps(f"Successfully decrypted {key} to {decrypted_key}")
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }

def mock_decrypt(content):
    """
    Mock decryption function.
    In a real implementation, this would use actual decryption logic.
    """
    # For this exercise, we're just returning the content as is
    # In a real scenario, you would implement actual decryption here
    return content