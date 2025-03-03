Testing Instructions
This document provides detailed instructions for deploying and testing the AWS Transfer and Lambda decryption solution.
Deployment
Prerequisites

AWS CLI installed and configured with appropriate permissions
SSH client for SFTP testing
An AWS account
Permissions to create IAM roles, S3 buckets, Lambda functions, and Transfer Family resources

Deployment Steps:

1. Clone the Repository
git clone https://github.com/your-username/aws-transfer-lambda-project.git
cd aws-transfer-lambda-project

2. Deploy the CloudFormation Stack
aws cloudformation create-stack \
  --stack-name aws-transfer-lambda-stack \
  --template-body file://cloudformation/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=ProjectName,ParameterValue=file-decryption \
               ParameterKey=SftpUserName,ParameterValue=sftpuser

3. Wait for Stack Creation
aws cloudformation wait stack-create-complete --stack-name aws-transfer-lambda-stack

4. Retrieve Stack Outputs
aws cloudformation describe-stacks \
  --stack-name aws-transfer-lambda-stack \
  --query "Stacks[0].Outputs" \
  --output table

Note the following values from the outputs:

TransferServerEndpoint: The server ID of your SFTP server
FileBucketName: The name of your S3 bucket
SftpEndpoint: The full SFTP endpoint for connecting


5. Set Up SSH Key Authentication
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
  --username sftpuser \
  --ssh-public-key-body file://sftp_key.pub


Testing the Solution
Test 1: Basic File Upload and Decryption

Create a Test File
echo "This is a test encrypted file" > test_file.txt

Upload the File via SFTP
# Get the SFTP endpoint
SFTP_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name aws-transfer-lambda-stack \
  --query "Stacks[0].Outputs[?OutputKey=='SftpEndpoint'].OutputValue" \
  --output text)

# Connect via SFTP and upload the file
sftp -i sftp_key $SFTP_ENDPOINT
> put test_file.txt
> exit

Verify File Upload and Decryption
# Get the S3 bucket name
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name aws-transfer-lambda-stack \
  --query "Stacks[0].Outputs[?OutputKey=='FileBucketName'].OutputValue" \
  --output text)

# Check for the raw file
aws s3 ls s3://$BUCKET_NAME/raw/

# Check for the decrypted file (may take a few seconds to appear)
aws s3 ls s3://$BUCKET_NAME/decrypted/

Verify the Contents (optional)
# Download the decrypted file
aws s3 cp s3://$BUCKET_NAME/decrypted/test_file.txt ./decrypted_file.txt

# Compare the contents
cat decrypted_file.txt


Test 2: Verify Lambda Execution

Check CloudWatch Logs
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

Verify Successful Processing
Look for log entries that indicate:

The Lambda function received the event
The file was successfully read from S3
The file was successfully "decrypted"
The decrypted file was written to the destination



Test 3: Error Handling

Test Invalid File Path
Create a file in a different directory structure to verify the Lambda correctly filters out files not in the raw/ directory.
sftp -i sftp_key $SFTP_ENDPOINT
> mkdir test
> cd test
> put test_file.txt
> exit
Check the Lambda logs to verify that the function recognized the file is not in the raw/ directory and skipped processing it.

Cleanup
When you're finished testing, remove all resources to avoid ongoing charges:
# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name aws-transfer-lambda-stack

# Wait for stack deletion
aws cloudformation wait stack-delete-complete --stack-name aws-transfer-lambda-stack

Troubleshooting
Common Issues

SFTP Connection Issues

Verify your SSH key permissions (should be 400 or 600)
Ensure the public key was correctly imported
Check that you're using the correct endpoint


Lambda Not Processing Files

Check CloudWatch Logs for any errors
Verify EventBridge rule is correctly configured
Ensure the S3 bucket has EventBridge notifications enabled


Permission Denied Errors

Verify IAM roles have the correct permissions
Check Lambda execution role permissions for S3 access
Ensure SFTP user role has write permissions to the raw/ prefix


Files Not Appearing in Decrypted Folder

Check Lambda logs for execution errors
Verify the Lambda function's timeout isn't being reached
Check that the file was correctly uploaded to the raw/ directory