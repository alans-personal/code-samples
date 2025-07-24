# AWS Cost Project

A comprehensive AWS cost optimization and monitoring system that tracks resource usage across multiple accounts and generates cost reports.

## Contact

**Email:** alan.snyder@gmail.com

## Project Overview

This project helps provide insight into how to reduce AWS bills by using resources more efficiently from a cost perspective. It consists of several sub-projects that work together to provide comprehensive cost analysis and optimization recommendations.

## Technologies

**Infrastructure-as-Code:** AWS CloudFormation  
**Languages:** Python  
**Frameworks:** Pandas, NumPy, Jupyter Notebooks  
**AWS Services:** Lambda, DynamoDB, S3, CloudWatch, CodePipeline, Cost Explorer API

## AWS Services Used

- **Lambda:** Scheduled functions for data collection and processing
- **DynamoDB:** Storage for usage data and cost metrics
- **S3:** Report storage and artifact management
- **CloudWatch:** Monitoring and alerting
- **CodePipeline:** Automated deployment pipeline
- **Cost Explorer API:** AWS cost and usage data retrieval
- **IAM:** Security roles and permissions

## Project Structure

```
/py_src - Python Lambda functions and utilities
/infra - CloudFormation templates
/scripts - Deployment and utility scripts
/jupyter_notebooks - Data analysis notebooks
/zip_code - Build artifacts for deployment
```

## Sub-Projects

### A) Hourly Usage Data Collection
CRON-based Lambda functions that record usage of AWS resources that can be purchased with Reserved capacity more cheaply.

### B) Cost Reports
Automated reports sent to managers and engineers detailing:
- Costs for their AWS accounts
- Total AWS resource usage
- Spend_Category tag coverage
- Cost estimates for micro-services

### C) Micro-Service Cost Tracking
Tracks Docker container usage logging to provide cost estimates for individual micro-services.

### D) Cost Panda with Jupyter Notebook
Loads billing files into formats for quick data analysis and report generation.

## AWS Resources Tracked

| # | AWS Resource | Tracking Frequency | Key Prefix |
|---:| --- |:---:| --- |
| 1 | EC2 | hourly | ec2 & ec2os |
| 2 | RDS | hourly | rds |
| 3 | DynamoDB Provisioned Capacity | hourly | dynamodb |
| 4 | Elasticache (Redis clusters) | hourly | elasticache |
| 5 | Elastic Search Service | daily | es |
| 6 | Redshift Nodes | daily | redshift |

## Scripts and Utilities

### Deployment Scripts

#### **`push_aws_cost_to_s3.py`**
Main deployment script that packages and uploads code to S3 for CodePipeline deployment:
- Creates temporary directory structure
- Copies Python source code and dependencies
- Updates build timestamps and version information
- Zips the application and uploads to pipeline S3 bucket
- Cleans up temporary files

#### **`git_commit_then_push_code.py`**
Automated git workflow script:
- Commits local changes with timestamp
- Pushes to remote repository
- Triggers deployment pipeline

### Utility Scripts

#### **`push_aws_cost_to_s3`** (Bash wrapper)
Simple bash wrapper for the Python deployment script.

#### **`git_commit_then_push_code`** (Bash wrapper)
Simple bash wrapper for the git workflow script.

## Code Locations

### Main Application Code
- **Lambda Function:** `py_src/awscost_lambda_function.py` - Main entry point for all Lambda operations
- **Controller:** `py_src/awscost_controller.py` - Orchestrates data collection and processing
- **Pipeline:** `py_src/awscost-pipeline.py` - Pipeline automation and workflow management
- **Panda Lambda:** `py_src/panda_lambda_function.py` - Jupyter notebook integration

### Utility Modules
- **AWS Utilities:** `py_src/util/aws_util.py` - Common AWS operations
- **Cost Helper:** `py_src/util/awscost_helper_util.py` - Cost analysis utilities
- **Account Management:** `py_src/util/aws_accounts.py` - Multi-account management

### Infrastructure
- **CloudFormation Stack:** `infra/aws-cost.stack.yaml` - Complete infrastructure definition

### Scripts
- **Deployment:** `scripts/push_aws_cost_to_s3.py`
- **Git Workflow:** `scripts/git_commit_then_push_code.py`
- **Bash Wrappers:** `scripts/push_aws_cost_to_s3`, `scripts/git_commit_then_push_code`

## Data Storage

### DynamoDB Tables

#### AWSCost Table
Stores hourly usage data with the following key format:
- **Primary Key:** `awsResource` (String)
- **Sort Key:** `time` (String)

Example keys:
- `ec2:asnyder:us-east-1` - EC2 Instance usage by Availability Zones
- `rds:<AWS_ACCOUNT_ID>:us-west-2` - RDS database nodes per AWS account
- `dynamodb:asnyder:us-east-1` - DynamoDB Provisioned Capacity

#### AWSCostMap Table
Generic mapping table for cost associations:
- **Primary Key:** `id` (String)
- Stores mappings like EC2 AMI IDs to OS types

## Reserved Instance Tracking

The system tracks various Reserved Instance types:

| Type | Key Prefix | Value Format | Description |
|:---:|:---:|:---:|:---|
| EC2 | ec2 | c4.large:us-west-2a | Includes AZ |
| EC2 | ec2os | linux-c4.large | Includes OS estimate |
| EC2 RIs | ri-ec2 | linux-t2.small | Includes OS |
| RDS | rds | db.r4.large:aurora-mysql | Includes DB engine |
| Elasticache | elasticache | cache.r4.large | Redis/Memcache nodes |
| Elastic Search | es | m4.large.elasticsearch | ES service nodes |
| Redshift | redshift | dc2.8xlarge | Redshift node types |
| DynamoDB | dynamodb | write_capacity | Read/write capacity units |

## Deployment Process

1. **Update Code:**
   ```bash
   cd scripts
   python git_commit_then_push_code.py
   ```

2. **Deploy to S3:**
   ```bash
   python push_aws_cost_to_s3.py
   ```

3. **Monitor Pipeline:**
   - Check AWS CodePipeline console for deployment status
   - Monitor CloudWatch logs for Lambda execution

## Reports and Outputs

### Excel Reports
Generated reports include:
- **AwsRIUsageReport:** Roku-level reports with pages for all regions and resource types
- **P95 Statistics:** Summary statistics for purchase options
- **Cost Explorer Integration:** Coverage, utilization, and recommendation reports

### S3 Storage
Reports are stored in the `AWSCost` S3 bucket with organized structure for easy access and analysis.

## Monitoring and Alerting

### CloudWatch Integration
- Lambda function monitoring and alerting
- Custom metrics for cost tracking
- Automated alerting for cost thresholds

### Health Checks
- Lambda function health monitoring
- DynamoDB table performance metrics
- S3 bucket access monitoring

## Security

- IAM roles follow least privilege principle
- DynamoDB encryption at rest
- S3 bucket encryption and access controls
- VPC isolation for Lambda functions
- Regular security updates and patches

## Cost Optimization Features

### Reserved Instance Analysis
- Tracks current Reserved Instance usage
- Identifies opportunities for new purchases
- Monitors utilization and coverage

### Tag-Based Cost Allocation
- Spend_Category tag tracking
- Team-based cost reporting
- Resource ownership identification

### Micro-Service Cost Tracking
- Docker container usage monitoring
- Per-service cost breakdown
- Optimization recommendations

## Troubleshooting

### Common Issues
1. **Lambda Timeout:** Monitor function execution time and memory usage
2. **Data Collection Gaps:** Check CloudWatch logs for Lambda errors
3. **Report Generation Issues:** Verify DynamoDB table access and S3 permissions

### Debug Commands
```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/awscost"

# Verify DynamoDB data
aws dynamodb scan --table-name AWSCost --limit 10

# Check S3 bucket contents
aws s3 ls s3://awscost-pipeline-source/
```

## Future Enhancements

- Budget API integration for alerts
- Slack command integration for cost queries
- Jupyter interface for custom report creation
- Enhanced micro-service cost tracking
- Real-time cost monitoring dashboard
