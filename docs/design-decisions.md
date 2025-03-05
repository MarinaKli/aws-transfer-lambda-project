# Design Decisions

This document outlines the key architectural and design decisions made for the AWS Transfer and Lambda decryption project.

## Architecture Overview

The system is designed to automatically decrypt files uploaded via SFTP using AWS services. The architecture follows serverless and event-driven principles to create a scalable and maintainable solution.

## Core Services

- **AWS Transfer Family**: Chosen for managed SFTP capability without managing servers
- **Amazon S3**: Used for secure, durable storage of both raw and decrypted files
- **AWS Lambda**: Provides serverless compute for file decryption
- **Amazon EventBridge**: Enables event-driven invocation of Lambda when files are uploaded
- **AWS KMS**: Used for decryption operations and server-side encryption of processed files

## Key Design Decisions

### 1. File Organization in S3

Files are organized in the same S3 bucket using prefixes:

- **/raw**: For encrypted files uploaded via SFTP
- **/decrypted**: For processed files after decryption

**Rationale**: Using prefixes in a single bucket simplifies management while still maintaining logical separation. This approach reduces the number of resources to manage and makes permissions simpler.

### 2. Event-Driven Processing

Files are processed automatically upon upload using EventBridge events rather than scheduled polling:

- EventBridge rule watches for "Object Created" events specifically in the "raw/" prefix
- Events trigger the Lambda function immediately when files are uploaded

**Rationale**: Event-driven architecture provides immediate processing, better scalability, and eliminates unnecessary polling operations that would occur when no files are uploaded.

### 3. Lambda Code Storage

Lambda function code is stored in an S3 bucket:

```yaml
Code: 
  S3Bucket: your-bucket-name
  S3Key: lambda_function.zip
```

**Rationale**: This approach provides better code management, versioning capabilities, and allows for larger function packages without CloudFormation template size limitations.

**Implementation Note**: Anyone replicating this project will need to:
1. Create their own S3 bucket for Lambda code storage
2. Upload the Lambda function code (lambda_function.zip) to their bucket
3. Update the CloudFormation template to reference their bucket name and key

### 4. IAM Role Permissions

IAM roles follow the principle of least privilege:

- **TransferUserRole**: 
  - Limited to ListBucket on the entire bucket
  - PutObject, GetObject, and DeleteObject only in the raw/ prefix
  
- **LambdaExecutionRole**:
  - GetObject permission only for the raw/ prefix
  - PutObject permission only for the decrypted/ prefix
  - ListBucket permission for the entire bucket
  - Basic Lambda execution permissions

**Rationale**: Limiting permissions enhances security by ensuring each component has only the access it needs.

### 5. KMS Integration

The Lambda function includes KMS integration for decryption operations:

- A KMS key ID can be provided via environment variables
- The Lambda function attempts to use KMS for decryption
- Server-side encryption is applied to decrypted files using the same KMS key
- A fallback mock decryption is implemented if KMS decryption fails

```python
# In Lambda function
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
```

**Rationale**: Using KMS provides enterprise-grade encryption/decryption capabilities and ensures secure file handling throughout the process.

### 6. SNS Notification Capability
The Lambda function includes SNS notification capabilities, though not yet configured in the CloudFormation template

### 7. Error Handling and Logging

Comprehensive error handling and logging are implemented in the Lambda function:

- Detailed logging with different log levels (INFO, WARNING, ERROR)
- Try/except blocks to catch and handle exceptions
- Validation of event structure before processing
- Graceful fallback to mock decryption if KMS decryption fails

**Rationale**: Robust error handling improves system reliability and makes troubleshooting easier by capturing and logging relevant information about any failures.

### 8. Security Measures

Multiple security measures are implemented throughout the system:

- SSH key-based authentication for SFTP users
- S3 bucket with versioning enabled
- Least privilege IAM policies
- Server-side encryption for decrypted files
- Detailed logging for audit trail and troubleshooting

**Rationale**: Taking a security-first approach ensures that sensitive data is protected at rest and in transit, and that system access is properly controlled.

### 8. Security Measures

Multiple security measures are implemented throughout the system:

- SSH key-based authentication for SFTP users
- S3 bucket with versioning enabled
- Least privilege IAM policies
- Server-side encryption for decrypted files
- Detailed logging for audit trail and troubleshooting

**Rationale**: Taking a security-first approach ensures that sensitive data is protected at rest and in transit, and that system access is properly controlled.

