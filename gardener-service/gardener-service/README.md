# Gardener Service

A container orchestration service that provides a unified interface for managing Docker deployments across AWS ECS clusters.

## Contact

**Email:** alan.snyder@gmail.com

## Project Overview

The Gardener Service provides a generic company-wide deployment service for Docker images that acts as a layer on top of AWS ECS clusters. It automates the deployment process and provides a unified interface for managing containerized applications across multiple environments.

## Technologies

**Infrastructure-as-Code:** AWS CloudFormation  
**Languages:** Java, Python, Bash  
**Frameworks:** Spring Boot (Java), Spark (Java)  
**AWS Services:** ECS, EC2, Lambda, S3, CodePipeline, CodeDeploy, DynamoDB, IAM

## AWS Services Used

- **ECS:** Container orchestration and management
- **EC2:** Application hosting and deployment targets
- **Lambda:** Pipeline automation and deployment orchestration
- **S3:** Source code storage and artifact management
- **CodePipeline:** Automated deployment pipeline
- **CodeDeploy:** Application deployment to EC2 instances
- **DynamoDB:** Configuration and state storage
- **IAM:** Security roles and permissions

## Project Structure

- **`api/`** - Java Spring Boot application providing the main Gardener service API
- **`py_src/`** - Python Lambda functions for pipeline automation and deployment orchestration
- **`infra/`** - CloudFormation templates for AWS infrastructure
- **`scripts/`** - Deployment and utility scripts

## Infrastructure Components

### CloudFormation Stacks

#### **`gardener-java-service.stack.yaml`**
Deploys the Java Spring Boot application infrastructure:
- EC2 instances for application hosting
- Security groups and IAM roles
- CodeDeploy configuration
- SSL certificate management

#### **`gardener-py-service.stack.yaml`**
Deploys Python Lambda functions and pipeline infrastructure:
- Lambda functions for automation
- S3 buckets for artifact storage
- CodePipeline configuration
- DynamoDB tables for state management

#### **`build-number-service.stack.yaml`**
Manages build numbering and versioning:
- DynamoDB table for build tracking
- Lambda functions for version management

#### **`farm-mulit-region.stack.yaml`**
Multi-region deployment configuration:
- Cross-region resource sharing
- Global load balancing setup

## Scripts and Utilities

### Deployment Scripts

#### **`push_java_gardener_to_s3.py`**
Packages and deploys the Java Spring Boot application to AWS S3 for CodePipeline integration:
- Creates a temporary directory structure matching Gradle requirements
- Copies Java source code, resources, and build configuration files
- Generates version information and build metadata
- Zips the application and uploads to the pipeline S3 bucket

#### **`push_py_gardener_to_s3.py`**
Packages and deploys the Python Lambda functions to AWS S3 for CodePipeline integration:
- Copies Python source code and dependencies
- Creates build information files
- Zips the Lambda code and uploads to the pipeline S3 bucket

#### **`gardener`**
System service script for managing the Gardener Java application on EC2 instances:
- **Usage:** `./gardener {start|stop|status|restart}`
- Manages the application as a background service with PID tracking
- Integrates with systemd for automatic startup/shutdown

### AWS CodeDeploy Scripts

#### **`codedeploy_java_before_install.sh`**
Pre-deployment setup script executed before application installation:
- Prepares SSL certificate directory structure
- Cleans up previous deployment artifacts
- Checks service status and stops existing instances

#### **`codedeploy_java_after_install.sh`**
Post-deployment cleanup script executed after application installation:
- Removes temporary deployment files
- Extracts the new application package
- Prepares the application for startup

#### **`codedeploy_java_application_start.sh`**
Application startup script for the deployed service:
- Restarts the Gardener service using the system service script
- Ensures proper service initialization

#### **`codedeploy_java_validate_service.sh`**
Health check script to validate successful deployment:
- Verifies the application process is running
- Checks service status and PID files

### Utility Scripts

#### **`ssl_update_key_store_entry.sh`**
Manages SSL certificates for secure communication:
- Downloads certificates from AWS Certificate Manager (ACM)
- Converts certificates to PKCS12 format
- Updates Java keystore with new certificate entries
- Handles certificate renewal and rotation

#### **`push_util.py`**
Shared utility functions for deployment operations:
- Common AWS S3 operations
- Version management and build numbering
- Logging and error handling utilities

## Code Locations

### Java Application
- **Main Application:** `api/src/main/java/com/asnyder/gardener/api/Main.java` - Spring Boot application entry point
- **DTOs:** `api/src/main/java/com/asnyder/gardener/api/dto/` - Data transfer objects
- **Build Configuration:** `api/build.gradle` - Gradle build configuration
- **Resources:** `api/src/main/resources/` - Configuration files and resources

### Python Lambda Functions
- **Main Lambda:** `py_src/gardener_lambda_function.py` - Lambda function entry point
- **Pipeline:** `py_src/gardener-pipeline.py` - Pipeline automation
- **Buildspec:** `py_src/buildspec.yml` - CodeBuild configuration
- **Utilities:** `py_src/util/` - Shared utility modules

### Infrastructure
- **Java Service Stack:** `infra/gardener-java-service.stack.yaml`
- **Python Service Stack:** `infra/gardener-py-service.stack.yaml`
- **Build Number Service:** `infra/build-number-service.stack.yaml`
- **Multi-Region Farm:** `infra/farm-mulit-region.stack.yaml`

### Scripts
- **Java Deployment:** `scripts/push_java_gardener_to_s3.py`
- **Python Deployment:** `scripts/push_py_gardener_to_s3.py`
- **Service Management:** `scripts/gardener`
- **CodeDeploy Scripts:** `scripts/codedeploy_*.sh`
- **SSL Management:** `scripts/ssl_update_key_store_entry.sh`
- **Utilities:** `scripts/push_util.py`

## Deployment Process

### Java Application Deployment
1. **Package Application:**
   ```bash
   cd scripts
   python push_java_gardener_to_s3.py
   ```

2. **Monitor Pipeline:**
   - Check AWS CodePipeline console for deployment status
   - Monitor CodeDeploy logs for deployment progress

3. **Verify Deployment:**
   ```bash
   sudo ./gardener status
   ```

### Python Lambda Deployment
1. **Package Lambda Functions:**
   ```bash
   cd scripts
   python push_py_gardener_to_s3.py
   ```

2. **Monitor Pipeline:**
   - Check AWS CodePipeline console for deployment status
   - Monitor CloudWatch logs for Lambda execution

## API Endpoints

### Health Check
- **GET** `/health` - Service health status

### Farm Management
- **GET** `/farm/:farmName/:az/state/desired` - Get desired state for a farm
- **POST** `/farm/:farmName/:az/state/desired` - Set desired state for a farm

### Service Management
- **GET** `/service/:serviceName/state` - Get service state
- **POST** `/service/:serviceName/deploy` - Deploy service

## Configuration

### Environment Variables
- `GARDENER_API_LAMBDA_FUNCTION` - Lambda function name for API calls
- `AWS_REGION` - AWS region for service deployment
- `ENVIRONMENT` - Environment (dev/prod) configuration

### SSL Configuration
- SSL certificates managed through AWS Certificate Manager
- Automatic certificate renewal and keystore updates
- Secure communication between services

## Security

- SSL certificates are managed through AWS Certificate Manager
- Service runs with minimal required permissions
- All deployments are logged and auditable
- Sensitive configuration is stored in AWS Parameter Store
- IAM roles follow least privilege principle

## Monitoring and Logging

### Application Logs
- Log files stored in `/home/ec2-user/gardener.%g.log`
- Log rotation with 5 files of 5MB each
- Structured logging with timestamps and log levels

### Health Monitoring
- Application health checks via `/health` endpoint
- Process monitoring with PID file tracking
- Service status monitoring via systemd integration

## Troubleshooting

### Common Issues
1. **Deployment Failures:** Check CodeDeploy logs and service status
2. **SSL Certificate Issues:** Verify ACM certificate status and keystore configuration
3. **Service Startup Issues:** Check application logs and systemd status

### Debug Commands
```bash
# Check service status
sudo ./gardener status

# View application logs
tail -f /home/ec2-user/gardener.0.log

# Check systemd status
sudo systemctl status gardener

# Verify SSL certificate
keytool -list -keystore /path/to/keystore.jks
```

## Integration Points

### ECS Integration
- Manages ECS cluster deployments
- Handles service scaling and updates
- Monitors container health and performance

### Lambda Integration
- Automated pipeline orchestration
- Deployment validation and rollback
- Cost optimization and monitoring

### DynamoDB Integration
- Configuration storage and retrieval
- State management and tracking
- Build number and version management

