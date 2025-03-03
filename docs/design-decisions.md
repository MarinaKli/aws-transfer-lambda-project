Design Decisions

This document outlines the key architectural and design decisions made for the AWS Transfer and Lambda decryption project.
Architecture Overview
The system is designed to automatically decrypt files uploaded via SFTP using AWS services. The architecture follows serverless and event-driven principles to create a scalable and maintainable solution.

Core Services

AWS Transfer Family: Chosen for managed SFTP capability without managing servers
Amazon S3: Used for secure, durable storage of both raw and decrypted files
AWS Lambda: Provides serverless compute for file decryption
Amazon EventBridge: Enables event-driven invocation of Lambda when files are uploaded

Key Design Decisions
1. File Organization in S3
We organize files in the same S3 bucket using prefixes:

/raw: For encrypted files uploaded via SFTP
/decrypted: For processed files after decryption

Rationale: Using prefixes in a single bucket simplifies management while still maintaining logical separation. This approach reduces the number of resources to manage and makes permissions simpler.
2. Event-Driven Processing
Files are processed automatically upon upload using EventBridge events rather than scheduled polling.
Rationale: Event-driven architecture provides immediate processing, better scalability, and eliminates unnecessary polling operations that would occur when no files are uploaded.
3. IAM Role Permissions
IAM roles follow the principle of least privilege:

SFTP users can only write to the /raw folder
Lambda function can read from /raw and write to /decrypted

Rationale: Limiting permissions enhances security by ensuring each component has only the access it needs.
4. Mock Decryption Implementation
For this exercise, we implemented a mock decryption function that simply passes through the content.
Rationale: In a production environment, this would be replaced with actual decryption using AWS KMS or another encryption service. The mock implementation demonstrates the architecture without requiring actual cryptographic keys.
5. Error Handling
Comprehensive error handling with detailed logging is implemented in the Lambda function.
Rationale: Robust error handling improves system reliability and makes troubleshooting easier by capturing and logging relevant information about any failures.
Future Enhancements
For a production environment, these enhancements would be considered:

AWS KMS Integration: Use AWS Key Management Service for secure key management
Dead Letter Queues: Add SQS dead letter queues for failed processing attempts
SNS Notifications: Send notifications on successful processing or errors
Enhanced Authentication: Use AWS Secrets Manager or Parameter Store for credential management
Multiple SFTP Users: Support multiple users with different permissions
Monitoring and Alerting: Add CloudWatch alarms and dashboards for system monitoring