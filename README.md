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

When a file is uploaded via SFTP, it is stored in the S3 bucket. This triggers an event that activates a Lambda function, which then decrypts the file and stores the decrypted version in the same bucket under a different prefix.


## Architecture
![AWS Transfer and Lambda Architecture](architecture/aws-transfer-lambda-architecture.svg)
## Prerequisites

- AWS CLI installed and configured
- Python 3.9 or later
- An AWS account with appropriate permissions
- SSH client for SFTP testing

## Project Structure

```
aws-transfer-lambda-project/
├── README.md
├── architecture/
│   └── aws-transfer-lambda-architecture.svg
├── cloudformation/
│   └── template.yaml
├── lambda/
│   └── lambda_function.py
└── docs/
    ├── design-decisions.md
    └── testing.md
```

## Deployment Instructions

To deploy this project to your AWS account:

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/aws-transfer-lambda-project.git
   cd aws-transfer-lambda-project
   ```

2. Deploy the CloudFormation stack:
   ```bash
   aws cloudformation create-stack \
     --stack-name aws-transfer-lambda-stack \
     --template-body file://cloudformation/template.yaml \
     --capabilities CAPABILITY_IAM \
     --parameters ParameterKey=ProjectName,ParameterValue=file-decryption \
                  ParameterKey=SftpUserName,ParameterValue=sftpuser
   ```

3. Wait for the deployment to complete:
   ```bash
   aws cloudformation wait stack-create-complete --stack-name aws-transfer-lambda-stack
   ```

4. Get the stack outputs for connection information:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-transfer-lambda-stack \
     --query "Stacks[0].Outputs" \
     --output table
   ```

5. Set up SSH key authentication for the SFTP user (see [Testing Instructions](docs/testing.md) for details).

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
- Future enhancement opportunities

## Cleaning Up

To remove all resources created by this project:

```bash
aws cloudformation delete-stack --stack-name aws-transfer-lambda-stack
```

## Security Considerations

- The SFTP server uses SSH key authentication
- IAM roles follow the principle of least privilege
- S3 bucket versioning is enabled to prevent accidental data loss
- Lambda error handling prevents information leakage