# gardener-service

All code for the Gardener APIs used by Farm. This includes infrastructure CloudFormation templates, Java code and Python code.

## Overview

The Gardener Service provides a generic company-wide deployment service for Docker images that acts as a layer on top of AWS ECS clusters. It automates the deployment process and provides a unified interface for managing containerized applications across multiple environments.

## Project Structure

- **`api/`** - Java Spring Boot application providing the main Gardener service API
- **`py_src/`** - Python Lambda functions for pipeline automation and deployment orchestration
- **`infra/`** - CloudFormation templates for AWS infrastructure
- **`scripts/`** - Deployment and utility scripts

## Scripts

### Deployment Scripts

#### **`push_java_gardener_to_s3.py`**
Packages and deploys the Java Spring Boot application to AWS S3 for CodePipeline integration.
- Creates a temporary directory structure matching Gradle requirements
- Copies Java source code, resources, and build configuration files
- Generates version information and build metadata
- Zips the application and uploads to the pipeline S3 bucket

#### **`push_py_gardener_to_s3.py`**
Packages and deploys the Python Lambda functions to AWS S3 for CodePipeline integration.
- Copies Python source code and dependencies
- Creates build information files
- Zips the Lambda code and uploads to the pipeline S3 bucket

#### **`gardener`**
System service script for managing the Gardener Java application on EC2 instances.
- **Usage:** `./gardener {start|stop|status|restart}`
- Manages the application as a background service with PID tracking
- Integrates with systemd for automatic startup/shutdown

### AWS CodeDeploy Scripts

#### **`codedeploy_java_before_install.sh`**
Pre-deployment setup script executed before application installation.
- Prepares SSL certificate directory structure
- Cleans up previous deployment artifacts
- Checks service status and stops existing instances

#### **`codedeploy_java_after_install.sh`**
Post-deployment cleanup script executed after application installation.
- Removes temporary deployment files
- Extracts the new application package
- Prepares the application for startup

#### **`codedeploy_java_application_start.sh`**
Application startup script for the deployed service.
- Restarts the Gardener service using the system service script
- Ensures proper service initialization

#### **`codedeploy_java_validate_service.sh`**
Health check script to validate successful deployment.
- Verifies the application process is running
- Checks service status and PID files

### Utility Scripts

#### **`ssl_update_key_store_entry.sh`**
Manages SSL certificates for secure communication.
- Downloads certificates from AWS Certificate Manager (ACM)
- Converts certificates to PKCS12 format
- Updates Java keystore with new certificate entries
- Handles certificate renewal and rotation

#### **`push_util.py`**
Shared utility functions for deployment operations.
- Common AWS S3 operations
- Version management and build numbering
- Logging and error handling utilities

## Quick Start

1. **Deploy Java Application:**
   ```bash
   cd scripts
   python push_java_gardener_to_s3.py
   ```

2. **Deploy Python Lambda Functions:**
   ```bash
   cd scripts
   python push_py_gardener_to_s3.py
   ```

3. **Manage Service (on EC2):**
   ```bash
   sudo ./gardener restart
   ```

## Infrastructure

The service uses AWS CodePipeline for automated deployments with the following components:
- **S3 Buckets:** Source code storage and artifact management
- **CodeBuild:** Compilation and packaging
- **CodeDeploy:** Application deployment to EC2 instances
- **ECS Clusters:** Container orchestration
- **Lambda Functions:** Pipeline automation and deployment orchestration

## Security

- SSL certificates are managed through AWS Certificate Manager
- Service runs with minimal required permissions
- All deployments are logged and auditable
- Sensitive configuration is stored in AWS Parameter Store

