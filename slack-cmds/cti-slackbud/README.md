# Slack Commands (CTI SlackBud)

A Slack bot application that provides various DevOps and AWS management commands through Slack integration.

## Contact

**Email:** alan.snyder@gmail.com

## Project Overview

CTI SlackBud is a comprehensive Slack bot that provides DevOps teams with easy access to AWS management, cost analysis, system monitoring, and various utility commands directly through Slack. It serves as a central hub for infrastructure management and team collaboration.

## Technologies

**Infrastructure-as-Code:** AWS CloudFormation  
**Languages:** Python, Bash  
**Frameworks:** Slack API, Serverless Framework  
**AWS Services:** Lambda, S3, CodePipeline, CodeBuild, IAM, EC2, ECS, CloudWatch

## AWS Services Used

- **Lambda:** Serverless function execution for all Slack commands
- **S3:** Source code storage and artifact management
- **CodePipeline:** Automated deployment pipeline
- **CodeBuild:** Code compilation and testing
- **IAM:** Security roles and permissions
- **EC2:** Instance management and monitoring
- **ECS:** Container service management
- **CloudWatch:** Monitoring and logging
- **DynamoDB:** Data storage for command state and configuration

## Project Structure

```
/slack_bud - Main Lambda function and command modules
/cmds - Individual command implementations
/util - Shared utility modules
/infra - CloudFormation templates
/scripts - Deployment and utility scripts
/ssm - SSM (Systems Manager) integration scripts
```

## Available Commands

### AWS Management Commands
- **`awsinfo`** - Get AWS account information and status
- **`awslogin`** - Generate temporary AWS credentials
- **`cost`** - AWS cost analysis and reporting
- **`spend`** - Detailed spending analysis
- **`ri`** - Reserved Instance management and analysis
- **`ebs`** - EBS volume management and optimization

### Infrastructure Commands
- **`farm`** - ECS farm management and deployment
- **`jupyter`** - Jupyter notebook instance management
- **`dsnacpu`** - CPU monitoring and analysis
- **`s3stats`** - S3 bucket statistics and usage

### Development Commands
- **`flamegraph`** - Performance profiling and flamegraph generation
- **`apps_flamegraph`** - Application-specific performance analysis
- **`uitests`** - UI testing automation
- **`p4`** - Perforce integration commands

### Utility Commands
- **`help`** - Command help and documentation
- **`version`** - Bot version information
- **`user`** - User management and permissions
- **`untagged`** - Resource tagging analysis
- **`cmd`** - Command execution and management
- **`patch`** - System patching and updates

## Scripts and Utilities

### Deployment Scripts

#### **`push_slack_bud_to_s3.py`**
Main deployment script that packages and uploads code to S3 for CodePipeline deployment:
- Creates temporary directory structure
- Copies Python source code and dependencies
- Updates build timestamps and version information
- Zips the application and uploads to pipeline S3 bucket
- Cleans up temporary files

#### **`push`** (Bash wrapper)
Simple bash wrapper for the Python deployment script.

### Utility Scripts

#### **`create_slack_cmd.py`**
Template generator for creating new Slack commands:
- Generates command class structure
- Creates import statements
- Sets up command registration
- Provides boilerplate code

#### **SSM Integration Scripts** (`ssm/`)
- **`ssm_remote.py`** - Remote execution via AWS Systems Manager
- **`ssm_flamegraph.py`** - Performance profiling via SSM

## Code Locations

### Main Application
- **Lambda Function:** `slack_bud/lambda_function.py` - Main entry point for all Slack commands
- **Long Tasks:** `slack_bud/lambda_longtasks.py` - Long-running task handler
- **Email Handler:** `slack_bud/lambda_function_send_email.py` - Email notification handler
- **JWT Refresh:** `slack_bud/lambda_jwt_refresh.py` - JWT token management

### Command Modules
- **Command Interface:** `slack_bud/cmds/cmd_interface.py` - Base command interface
- **Command Inputs:** `slack_bud/cmds/cmd_inputs.py` - Input parsing and validation
- **Individual Commands:** `slack_bud/cmds/cmds_*.py` - Specific command implementations

### Utility Modules
- **AWS Utilities:** `slack_bud/util/aws_util.py` - Common AWS operations
- **Slack UI:** `slack_bud/util/slack_ui_util.py` - Slack UI components
- **Bud Helper:** `slack_bud/util/bud_helper_util.py` - Core utility functions
- **JWT Utils:** `slack_bud/util/jwt_utils.py` - JWT token handling
- **LDAP Utils:** `slack_bud/util/ldap_utils.py` - LDAP integration

### Infrastructure
- **Pipeline Stack:** `infra/cti-slackbud-pipeline.stack.yaml` - Main deployment pipeline
- **Deploy Bucket:** `infra/cti-slackbud-deploy-bucket.stack.yaml` - S3 bucket configuration
- **Command Roles:** `infra/run-cmd-roles.stack.yaml` - IAM roles for commands

### Scripts
- **Deployment:** `scripts/push_slack_bud_to_s3.py`
- **Command Creation:** `scripts/create_slack_cmd.py`
- **SSM Scripts:** `scripts/ssm/ssm_*.py`

## Infrastructure Components

### CloudFormation Stacks

#### **`cti-slackbud-pipeline.stack.yaml`**
Main deployment pipeline that includes:
- CodePipeline for automated deployments
- CodeBuild for compilation and testing
- Lambda functions for deployment and testing
- S3 buckets for artifact storage
- IAM roles and policies

#### **`cti-slackbud-deploy-bucket.stack.yaml`**
S3 bucket configuration for deployment artifacts.

#### **`run-cmd-roles.stack.yaml`**
IAM roles and policies for command execution.

### Additional Infrastructure
- **Airflow Stacks:** `infra/dsna-airflow*.stack.yaml` - Data processing workflows
- **Jupyter Stack:** `infra/dea-jupyter.stack.yaml` - Jupyter notebook infrastructure
- **Tableau Automation:** `infra/dsna-tableau-automation.stack.yaml` - Reporting automation

## Deployment Process

1. **Package Application:**
   ```bash
   cd scripts
   python push_slack_bud_to_s3.py
   ```

2. **Monitor Pipeline:**
   - Check AWS CodePipeline console for deployment status
   - Monitor CloudWatch logs for Lambda execution
   - Verify Slack app integration

3. **Test Commands:**
   ```bash
   /slackbud help
   /slackbud version
   ```

## Command Development

### Creating New Commands

1. **Generate Command Template:**
   ```bash
   cd scripts
   python create_slack_cmd.py --name mycommand
   ```

2. **Implement Command Logic:**
   - Edit the generated command file
   - Add business logic and AWS integration
   - Implement error handling and validation

3. **Register Command:**
   - Add import statement to `lambda_function.py`
   - Add command mapping in the handler

### Command Structure
Each command follows a consistent pattern:
- Inherits from `CmdInterface`
- Implements `execute()` method
- Handles input validation
- Returns structured Slack responses

## Security

- JWT token validation for secure communication
- IAM roles with least privilege access
- Slack signature verification
- Encrypted environment variables
- Audit logging for all commands

## Monitoring and Logging

### CloudWatch Integration
- Lambda function monitoring and alerting
- Custom metrics for command usage
- Error tracking and alerting

### Slack Integration
- Command usage analytics
- User interaction tracking
- Error reporting to channels

## Troubleshooting

### Common Issues
1. **Command Timeout:** Check Lambda timeout settings and command complexity
2. **Permission Errors:** Verify IAM roles and policies
3. **Slack Integration Issues:** Check Slack app configuration and permissions

### Debug Commands
```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/slackbud"

# Test command locally
python -c "from slack_bud.cmds.cmds_help import CmdHelp; print('Command loaded successfully')"

# Verify Slack app configuration
curl -X POST https://slack.com/api/auth.test -H "Authorization: Bearer $SLACK_BOT_TOKEN"
```

## Integration Points

### AWS Services
- **EC2:** Instance management and monitoring
- **ECS:** Container service operations
- **CloudWatch:** Metrics and logging
- **Cost Explorer:** Cost analysis and reporting
- **Systems Manager:** Remote execution and management

### External Services
- **Slack:** Command interface and notifications
- **LDAP:** User authentication and authorization
- **JIRA:** Issue tracking and project management
- **Perforce:** Version control integration

## Performance Optimization

### Lambda Optimization
- Cold start minimization
- Memory allocation tuning
- Dependency optimization
- Connection pooling for AWS services

### Command Optimization
- Asynchronous execution for long-running tasks
- Caching for frequently accessed data
- Pagination for large result sets
- Background processing for heavy operations
