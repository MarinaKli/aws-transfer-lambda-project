# aws-transfer-lambda-project
AWS Transfer Family and Lambda function for file decryption using CloudFormation -assignment project
# AWS Transfer and Lambda Function Project

## Project Overview
Automated file transfer and decryption process using AWS Transfer Family, S3, EventBridge, and Lambda.

This project creates an SFTP server using AWS Transfer Family that automatically decrypts files when they are uploaded. The system consists of:

- AWS Transfer Family SFTP server for secure file uploads
- S3 bucket for file storage
- Lambda function for automatic file decryption
- EventBridge rule to trigger the Lambda function
- Optional SNS notifications for file processing events

When a file is uploaded via SFTP, it is stored in the S3 bucket. This triggers an event that activates a Lambda function, which then decrypts the file and stores the decrypted version in the same bucket under a different prefix.


## Architecture
![AWS Transfer and Lambda Architecture](architecture/aws-transfer-lambda-architecture.svg)


## Architecture Components

AWS Transfer Family (SFTP Server)

Provides secure file transfer capabilities
Authenticates users with SSH key pairs
Stores uploaded files in an S3 bucket


Amazon S3

Stores both encrypted (raw) and decrypted files
Uses separate prefixes for organization (/raw and /decrypted)
Triggers events when new files are uploaded


AWS Lambda

Processes files when they are uploaded
Implements decryption logic using KMS
Stores decrypted files back to S3
Lambda code stored in a dedicated S3 bucket


AWS Key Management Service (KMS)

Manages encryption keys
Provides secure decryption capabilities
Integrates with Lambda for file processing


Amazon EventBridge

Detects S3 object creation events
Triggers Lambda function when files are uploaded
Filters events to only process files in /raw prefix

Amazon SNS (Optional)

Lambda includes code for sending notifications
Can send alerts for successful or failed file processing
Not configured in the default CloudFormation template

IAM Roles and Permissions

Transfer User Role: Controls SFTP user access to S3
Lambda Execution Role: Provides Lambda access to S3, KMS, and logs

## Prerequisites

- AWS CLI installed and configured
- Python 3.9 or later
- An AWS account with appropriate permissions
- SSH client for SFTP testing

## Project Structure

```
aws-transfer-lambda-project/
├── README.md
├── architecture/               # Architecture diagrams
├── cloudformation/             # CloudFormation templates
├── docs/
│   ├── design-decisions.md     # Architecture and design explanations
│   └── testing.md              # Testing procedures and deployment instructions
├── lambda/                     # Lambda function code
├── policies/                   # IAM policy definitions and samples
└── .gitignore                  # Excludes test files and keys
```

## Deployment Instructions

To deploy this project to your AWS account:

1. Clone this repository:
   ```bash
   git clone https://github.com/MarinaKli/aws-transfer-lambda-project.git
   cd aws-transfer-lambda-project
   ```
2. Create an S3 bucket for Lambda code:

   ```bash
   aws s3 mb s3://your-lambda-code-bucket-name
   ```
3. Package and upload the Lambda function:

   ```bash 
   cd lambda
   zip -r lambda_function.zip lambda_function.py
   aws s3 cp lambda_function.zip s3://your-lambda-code-bucket-name/
   cd ..
   ```

4. Deploy the CloudFormation stack:
   ```bash
   aws cloudformation create-stack \
  --stack-name aws-transfer-lambda-stack \
  --template-body file://cloudformation/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=ProjectName,ParameterValue=file-decryption \
               ParameterKey=SftpUserName,ParameterValue=sftpuser \
               ParameterKey=LambdaCodeBucket,ParameterValue=your-lambda-code-bucket \
               ParameterKey=LambdaCodeKey,ParameterValue=lambda_function.zip
   ```

5. Wait for the deployment to complete:
   ```bash
   aws cloudformation wait stack-create-complete --stack-name aws-transfer-lambda-stack
   ```

6. Get the stack outputs for connection information:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs" \
     --output table
   ```

7. Set up SSH key authentication for the SFTP user (see [Testing Instructions](docs/testing.md) for details).

## Testing

To test the solution:

1. Generate and register an SSH key for SFTP authentication
2. Upload a file via SFTP to the generated endpoint
3. Verify that the file appears in both the raw and decrypted folders in S3
4. Check Lambda logs to verify successful processing

For detailed testing instructions, see [Testing Documentation](docs/testing.md).

## Design Decisions

Key architectural and design decisions are documented in [Design Decisions](docs/design-decisions.md), including:

- Service selection rationale
- File organization strategy
- Security considerations
- Error handling approach
- KMS integration details

## Enhancements
The current implementation can be enhanced with:
1. KMS Key Configuration
2. SNS Notifications

## Cleaning Up

To remove all resources created by this project:

1. Empty the S3 bucket first (required before bucket deletion):
   ```bash
   # Get the S3 bucket name
   BUCKET_NAME=$(aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs[?OutputKey=='FileBucketName'].OutputValue" \
     --output text)
   
   # Empty the S3 bucket
   aws s3 rm s3://$BUCKET_NAME --recursive
   ```

2. Delete the CloudFormation stack:
   ```bash 
   aws cloudformation delete-stack --stack-name aws-transfer-lambda-stack
   ```
   
3. Delete the Lambda code bucket (if you no longer need it):
   ```bash
   # Empty the bucket first
   aws s3 rm s3://your-lambda-code-bucket-name --recursive
   
   # Delete the bucket
   aws s3 rb s3://your-lambda-code-bucket-name
   ```
  

## Security Considerations

- SFTP provides secure file transmission
- SSH key-based authentication for SFTP users
- AWS KMS for key management and decryption
- Least Privilege Access: IAM roles with minimal required permissions
- S3 Bucket Protection:
       - Bucket versioning enabled to prevent accidental data loss
       - Server-side encryption enabled by default
       - Public access blocks in place
