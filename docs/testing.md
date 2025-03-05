# Testing Instructions

This document provides detailed instructions for deploying and testing the AWS Transfer and Lambda decryption solution.

## Deployment

### Prerequisites

- AWS CLI installed and configured with appropriate permissions
- SSH client for SFTP testing
- An AWS account
- Permissions to create IAM roles, S3 buckets, Lambda functions, and Transfer Family resources

### Deployment Steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/MarinaKli/aws-transfer-lambda-project.git
   cd aws-transfer-lambda-project
   ```

2. **Create an S3 Bucket for Lambda Code**
   ```bash
   aws s3 mb s3://your-lambda-code-bucket-name
   ```

3. **Package and Upload the Lambda Function**
   ```bash
   cd lambda
   zip -r lambda_function.zip lambda_function.py
   aws s3 cp lambda_function.zip s3://your-lambda-code-bucket-name/
   cd ..
   ```

4. **Deploy the CloudFormation Stack**
   ```bash
   aws cloudformation create-stack \
     --stack-name aws-transfer-lambda-stack \
     --template-body file://cloudformation/template.yaml \
     --capabilities CAPABILITY_IAM \
     --parameters ParameterKey=ProjectName,ParameterValue=file-decryption \
                  ParameterKey=SftpUserName,ParameterValue=sftpuser \
                  ParameterKey=LambdaCodeBucket,ParameterValue=your-lambda-code-bucket-name \
                  ParameterKey=LambdaCodeKey,ParameterValue=lambda_function.zip
   ```

5. **Wait for Stack Creation**
   ```bash
   aws cloudformation wait stack-create-complete --stack-name aws-transfer-lambda-stack
   ```

6. **Retrieve Stack Outputs**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs" \
     --output table
   ```

   Note the following values from the outputs:
   - TransferServerEndpoint: The server ID of your SFTP server
   - FileBucketName: The name of your S3 bucket
   - SftpEndpoint: The full SFTP endpoint for connecting

7. **Set Up SSH Key Authentication**
   ```bash
   # Generate an SSH key pair
   ssh-keygen -t rsa -b 4096 -f sftp_key

   # Get the server ID from the stack outputs
   SERVER_ID=$(aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs[?OutputKey=='TransferServerEndpoint'].OutputValue" \
     --output text)

   # Import the public key to your SFTP user
   aws transfer import-ssh-public-key \
     --server-id $SERVER_ID \
     --user-name sftpuser \
     --ssh-public-key-body file://sftp_key.pub
   ```

## Testing the Solution

### Test 1: Basic File Upload and Decryption

1. **Create a Test File**
   ```bash
   echo "This is a test encrypted file" > test_plaintext.txt
   ```

2. **Upload the File via SFTP**
   ```bash
   # Get the SFTP endpoint
   SFTP_ENDPOINT=$(aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs[?OutputKey=='SftpEndpoint'].OutputValue" \
     --output text)

   # Connect via SFTP and upload the file
   sftp -i sftp_key $SFTP_ENDPOINT
   > put test_plaintext2.txt
   > exit
   ```

3. **Verify File Upload and Decryption**
   ```bash
   # Get the S3 bucket name
   BUCKET_NAME=$(aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs[?OutputKey=='FileBucketName'].OutputValue" \
     --output text)

   # Check for the raw file
   aws s3 ls s3://$BUCKET_NAME/raw/

   # Check for the decrypted file (may take a few seconds to appear)
   aws s3 ls s3://$BUCKET_NAME/decrypted/
   ```

4. **Verify the Contents (optional)**
   ```bash
   # Download the decrypted file
   aws s3 cp s3://$BUCKET_NAME/decrypted/test_plaintext.txt ./decrypted_file.txt

   # View the contents
   cat decrypted_file.txt
   ```
   
   Note: Since mock decryption simply reverses the content, the decrypted file should contain the reversed text of the original file.

### Test 2: KMS Encryption and Decryption (Optional)

If you want to test with actual KMS encryption:

1. **Create a KMS key** (if you don't already have one):
   ```bash
   # Create a KMS key
   KEY_ID=$(aws kms create-key --description "Key for SFTP decryption testing" --query KeyMetadata.KeyId --output text)
   
   # Add an alias to make it easier to reference
   aws kms create-alias --alias-name alias/sftp-decryption --target-key-id $KEY_ID
   
   echo "Created KMS key: $KEY_ID"
   ```

2. **Encrypt a test file using KMS**:
   ```bash
   # Create a test file
   echo "This is KMS encrypted content" > kms_test.txt
   
   # Encrypt the file using KMS
   aws kms encrypt \
     --key-id $KEY_ID \
     --plaintext fileb://kms_test.txt \
     --output text \
     --query CiphertextBlob | base64 --decode > kms_encrypted.bin
   ```

3. **Update the Lambda function with KMS key**:
   ```bash
   # Update the Lambda function to use your KMS key

   aws lambda update-function-configuration \
     --function-name file-decryption-decryption-function \
     --environment "Variables={OUTPUT_PREFIX=decrypted,KMS_KEY_ID=$KEY_ID}"
   ```

4. **Upload the encrypted file via SFTP**:
   ```bash
   sftp -i sftp_key $SFTP_ENDPOINT
   > put kms_encrypted.bin
   > exit
   ```

5. **Verify decryption**:
   ```bash
   # Check CloudWatch logs to see decryption process
   # Download and check the decrypted file
   aws s3 cp s3://$BUCKET_NAME/decrypted/kms_encrypted.bin ./kms_decrypted.txt
   
   # View the decrypted content
   cat kms_decrypted.txt
   ```

### Test 3: Verify Lambda Execution

1. **Check CloudWatch Logs**
   ```bash
   # Get the Lambda function name
   FUNCTION_NAME=$(aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs[?OutputKey=='DecryptionFunctionName'].OutputValue" \
     --output text)

   # Get the most recent log stream
   LOG_STREAM=$(aws logs describe-log-streams \
     --log-group-name /aws/lambda/$FUNCTION_NAME \
     --order-by LastEventTime \
     --descending \
     --limit 1 \
     --query "logStreams[0].logStreamName" \
     --output text)

   # View the logs
   aws logs get-log-events \
     --log-group-name /aws/lambda/$FUNCTION_NAME \
     --log-stream-name $LOG_STREAM
   ```

2. **Verify Successful Processing**
   
   Look for log entries that indicate:
   - The Lambda function received the event (look for: `"Received event:"`)
   - The file was successfully read from S3 (look for: `"Processing file: raw/test_plaintext.txt"`)
   - The file was successfully "decrypted" (if using mock decryption, there won't be explicit confirmation)
   - The decrypted file was written to the destination (look for: `"Decrypted file saved as: decrypted/test_plaintext.txt"`)
   - A successful response (look for: `"Successfully decrypted raw/test_plaintext.txt to decrypted/test_plaintext.txt"`)
   
   If there are errors, you'll see:
   - Warning or error level log messages
   - Python tracebacks indicating where the error occurred
   - Messages beginning with "Error processing file:" followed by the specific error

### Test 3: Error Handling

1. **Test Invalid File Path**
   
   Create a file in a different directory structure to verify the Lambda correctly filters out files not in the raw/ directory.
   
   ```bash
   sftp -i sftp_key $SFTP_ENDPOINT
   > mkdir test
   > cd test
   > put test_plaintext.txt
   > exit
   ```
   
   Check the Lambda logs to verify that the function recognized the file is not in the raw/ directory and skipped processing it.

## Cleanup

When you're finished testing, remove all resources to avoid ongoing charges:

1. **Empty the file storage S3 bucket first** (required before bucket deletion):
   ```bash
   # Get the S3 bucket name
   BUCKET_NAME=$(aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs[?OutputKey=='FileBucketName'].OutputValue" \
     --output text)
   
   # Empty the S3 bucket
   aws s3 rm s3://$BUCKET_NAME --recursive
   ```

2. **Delete the CloudFormation stack**:
   ```bash
   # Delete the CloudFormation stack
   aws cloudformation delete-stack --stack-name aws-transfer-lambda-stack

   # Wait for stack deletion
   aws cloudformation wait stack-delete-complete --stack-name aws-transfer-lambda-stack
   ```

3. **Delete the Lambda code bucket** (if you no longer need it):
   ```bash
   # Empty the bucket first
   aws s3 rm s3://your-lambda-code-bucket-name --recursive
   
   # Delete the bucket
   aws s3 rb s3://your-lambda-code-bucket-name
   ```

## Troubleshooting

### Common Issues

1. **SFTP Connection Issues**
   - Verify your SSH key permissions (should be 400 or 600)
   - Ensure the public key was correctly imported
   - Check that you're using the correct endpoint

2. **Lambda Not Processing Files**
   - Check CloudWatch Logs for any errors
   - Verify EventBridge rule is correctly configured
   - Ensure the S3 bucket has EventBridge notifications enabled

3. **Permission Denied Errors**
   - Verify IAM roles have the correct permissions
   - Check Lambda execution role permissions for S3 access
   - Ensure SFTP user role has write permissions to the raw/ prefix

4. **Files Not Appearing in Decrypted Folder**
   - Check Lambda logs for execution errors
   - Verify the Lambda function's timeout isn't being reached
   - Check that the file was correctly uploaded to the raw/ directory
   
5. **Lambda Deployment Issues**
   - Ensure the Lambda code is correctly zipped (with the .py file at the root level of the zip)
   - Verify your S3 bucket exists and the upload was successful
   - Check that the Lambda code key in the CloudFormation parameters matches your uploaded file
