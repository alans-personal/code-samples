# Code Samples

A collection of sample projects demonstrating various AWS services, infrastructure-as-code patterns, and application frameworks.

## Contact

**Email:** alan.snyder@gmail.com

## Project Overview

This repository contains five distinct projects showcasing different approaches to cloud infrastructure and application development:

### 1. **AWS CDK Loki Create** (`aws-cdk-loki-create/`)
A logging infrastructure project that sets up Grafana and Loki on EC2 instances for centralized log collection and visualization.

**Infrastructure-as-Code:** AWS CDK (Python)  
**Languages:** Python, Bash  
**Frameworks:** Grafana, Loki  
**AWS Services:** EC2, S3, DynamoDB, IAM, VPC, CloudFormation Exports

### 2. **AWS Cost** (`awscost/`)
A comprehensive AWS cost optimization and monitoring system that tracks resource usage across multiple accounts and generates cost reports.

**Infrastructure-as-Code:** AWS CloudFormation  
**Languages:** Python  
**Frameworks:** Pandas, NumPy, Jupyter Notebooks  
**AWS Services:** Lambda, DynamoDB, S3, CloudWatch, CodePipeline, Cost Explorer API

### 3. **Gardener Service** (`gardener-service/`)
A container orchestration service that provides a unified interface for managing Docker deployments across AWS ECS clusters.

**Infrastructure-as-Code:** AWS CloudFormation  
**Languages:** Java, Python, Bash  
**Frameworks:** Spring Boot (Java), Spark (Java)  
**AWS Services:** ECS, EC2, Lambda, S3, CodePipeline, CodeDeploy, DynamoDB, IAM

### 4. **Slack Commands** (`slack-cmds/`)
A Slack bot application that provides various DevOps and AWS management commands through Slack integration.

**Infrastructure-as-Code:** AWS CloudFormation  
**Languages:** Python, Bash  
**Frameworks:** Slack API, Serverless Framework  
**AWS Services:** Lambda, S3, CodePipeline, CodeBuild, IAM, EC2, ECS, CloudWatch

### 5. **Stripe Cognito Terraform** (`stripe-cognito-terraform/`)
A full-stack web application demonstrating user authentication with AWS Cognito and payment processing with Stripe.

**Infrastructure-as-Code:** Terraform  
**Languages:** Python  
**Frameworks:** FastAPI, NiceGUI, Docker  
**AWS Services:** AppRunner, ECR, Cognito, VPC, IAM

## Quick Navigation

- [AWS CDK Loki Create](./aws-cdk-loki-create/ec2-loki/README.md)
- [AWS Cost](./awscost/awscost/README.md)
- [Gardener Service](./gardener-service/gardener-service/README.md)
- [Slack Commands](./slack-cmds/cti-slackbud/README.md)
- [Stripe Cognito Terraform](./stripe-cognito-terraform/stripe-test-env/README.md)

## Common Patterns

All projects demonstrate:
- Infrastructure-as-Code best practices
- AWS service integration
- Automated deployment pipelines
- Security best practices
- Monitoring and logging
- Cost optimization strategies
