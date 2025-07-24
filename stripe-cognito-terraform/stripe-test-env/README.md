# Stripe Cognito Terraform

A full-stack web application demonstrating user authentication with AWS Cognito and payment processing with Stripe.

## Contact

**Email:** alan.snyder@gmail.com

## Project Overview

This is a full-stack application built with FastAPI, NiceGUI, and AWS infrastructure that demonstrates a complete sign-up flow with AWS Cognito authentication and Stripe API payment processing. The project follows a well-defined structure for maintainability and scalability.

## Technologies

**Infrastructure-as-Code:** Terraform  
**Languages:** Python  
**Frameworks:** FastAPI, NiceGUI, Docker  
**AWS Services:** AppRunner, ECR, Cognito, VPC, IAM

## AWS Services Used

- **AppRunner:** Containerized application hosting and scaling
- **ECR:** Container image registry and management
- **Cognito:** User authentication and management
- **VPC:** Network isolation and security
- **IAM:** Security roles and permissions
- **Certificate Manager:** SSL certificate management

## Project Structure

```
/infra - Terraform code for AWS infrastructure
/src - Python application source code (FastAPI + NiceGUI)
/test - Pytest test suite
/prompts - Project documentation and AI interaction prompts
/docs - Project documentation and specifications
/images - Application screenshots and diagrams
```

## Infrastructure Components

### Terraform Modules

#### **VPC Module** (`infra/modules/vpc/`)
Creates the network infrastructure:
- VPC with public and private subnets
- Internet Gateway and NAT Gateway
- Route tables and security groups
- Network ACLs for traffic control

#### **Cognito Module** (`infra/modules/cognito/`)
Sets up user authentication:
- User Pool with custom attributes
- App Client with OAuth configuration
- Identity Pool for AWS service access
- Password policies and MFA settings

#### **ECR Module** (`infra/modules/ecr/`)
Manages container registry:
- ECR repository for application images
- Lifecycle policies for image cleanup
- Repository permissions and access controls

#### **AppRunner Module** (`infra/modules/apprunner/`)
Deploys the application:
- AppRunner service configuration
- ECR integration for image deployment
- Environment variables and secrets management
- Auto-scaling and health check configuration

## Application Components

### FastAPI Backend
The application uses FastAPI as the backend framework:
- RESTful API endpoints
- WebSocket support for real-time features
- Middleware for CORS and authentication
- Request/response validation with Pydantic

### NiceGUI Frontend
Modern web interface built with NiceGUI:
- Reactive UI components
- Real-time updates and notifications
- Responsive design for mobile and desktop
- Built-in authentication flow integration

### Docker Containerization
Application is containerized for consistent deployment:
- Multi-stage Dockerfile for optimization
- Health check endpoints
- Environment-specific configurations
- Security best practices implementation

## Scripts and Utilities

### Deployment Scripts

#### **`build-and-push.sh`**
Automated Docker build and deployment script:
- Authenticates with ECR
- Builds Docker image with latest code
- Tags image for ECR repository
- Pushes image to ECR
- Triggers AppRunner deployment

#### **`test-local.sh`**
Local testing and development script:
- Builds Docker image locally
- Runs container on port 8000
- Tests health and root endpoints
- Opens application in browser
- Displays container logs

#### **`test-local-cleanup.sh`**
Cleanup script for local testing:
- Stops running containers
- Removes Docker images
- Cleans up temporary files

### Development Scripts

#### **Terraform Management**
```bash
# Initialize Terraform
cd infra
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy
```

## Code Locations

### Application Code
- **Main Application:** `src/main.py` - FastAPI application entry point
- **Requirements:** `requirements.txt` - Python dependencies
- **Dockerfile:** `Dockerfile` - Container configuration

### Infrastructure Code
- **Main Terraform:** `infra/main.tf` - Primary infrastructure configuration
- **Variables:** `infra/variables.tf` - Terraform variable definitions
- **Backend:** `infra/backend.tf` - Terraform state configuration
- **VPC Module:** `infra/modules/vpc/` - Network infrastructure
- **Cognito Module:** `infra/modules/cognito/` - Authentication setup
- **ECR Module:** `infra/modules/ecr/` - Container registry
- **AppRunner Module:** `infra/modules/apprunner/` - Application deployment

### Scripts
- **Docker Build:** `build-and-push.sh`
- **Local Testing:** `test-local.sh`
- **Cleanup:** `test-local-cleanup.sh`

### Documentation
- **Project Docs:** `docs/` - Comprehensive project documentation
- **Implementation:** `docs/Implementation.md` - Technical implementation details
- **UI/UX Docs:** `docs/UI_UX_doc.md` - User interface documentation
- **Stripe Integration:** `docs/stripe_*.md` - Payment processing documentation

## Deployment Process

### 1. Infrastructure Setup
```bash
cd infra
terraform init
terraform plan
terraform apply
```

### 2. Application Deployment
```bash
# Build and push Docker image
./build-and-push.sh

# Or manually:
docker build -t stripe-test .
docker tag stripe-test:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:latest
```

### 3. Configuration
- Update environment variables in AppRunner service
- Configure Stripe webhook endpoints
- Set up Cognito user pool settings

## Authentication Flow

### Cognito Integration
1. **User Registration:** Users sign up through Cognito
2. **Email Verification:** Cognito sends verification emails
3. **Password Reset:** Secure password reset flow
4. **JWT Tokens:** Authentication tokens for API access
5. **Session Management:** Automatic token refresh

### Security Features
- JWT token validation
- CORS configuration
- Rate limiting
- Input validation and sanitization
- Secure password policies

## Payment Processing

### Stripe Integration
- **Subscription Plans:** Trial, Basic, and Premium tiers
- **Webhook Handling:** Secure webhook processing
- **Payment Methods:** Credit card and digital wallet support
- **Invoice Management:** Automatic invoice generation
- **Refund Processing:** Automated refund handling

### Payment Flow
1. User selects subscription plan
2. Stripe Checkout session creation
3. Payment processing and validation
4. Webhook notification handling
5. Subscription status updates

## Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-west-2
ENVIRONMENT=production

# Cognito Configuration
COGNITO_USER_POOL_ID=us-west-2_xxxxxxxxx
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxx

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx

# Application Configuration
PORT=8000
```

### Terraform Variables
- `aws_region` - AWS region for deployment
- `environment` - Environment name (dev/staging/prod)
- `project` - Project identifier
- `vpc_cidr` - VPC CIDR block
- `tags` - Resource tagging

## Testing

### Local Testing
```bash
# Run local tests
./test-local.sh

# Clean up after testing
./test-local-cleanup.sh

# Run pytest tests
pytest test/
```

### Integration Testing
- Stripe webhook testing with ngrok
- Cognito authentication flow testing
- AppRunner deployment validation
- End-to-end user journey testing

## Monitoring and Logging

### Application Logging
- Structured logging with timestamps
- Log levels (INFO, WARNING, ERROR)
- Request/response logging
- Error tracking and alerting

### AWS Monitoring
- CloudWatch metrics and alarms
- AppRunner service monitoring
- ECR repository monitoring
- Cognito user pool analytics

## Security Considerations

### Infrastructure Security
- VPC isolation with private subnets
- Security groups with minimal access
- IAM roles with least privilege
- SSL/TLS encryption for all traffic

### Application Security
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF token validation
- Secure session management

### Data Protection
- PII data encryption at rest
- Secure transmission of sensitive data
- Regular security audits
- Compliance with data protection regulations

## Troubleshooting

### Common Issues
1. **Cognito Authentication Errors:** Check user pool configuration and client settings
2. **Stripe Webhook Failures:** Verify webhook endpoint and signature validation
3. **AppRunner Deployment Issues:** Check ECR image availability and service configuration
4. **Network Connectivity:** Verify VPC and security group settings

### Debug Commands
```bash
# Check AppRunner service status
aws apprunner describe-service --service-arn <SERVICE_ARN>

# View application logs
aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner"

# Test Cognito authentication
aws cognito-idp admin-get-user --user-pool-id <USER_POOL_ID> --username <USERNAME>

# Verify ECR image
aws ecr describe-images --repository-name stripe-test --region us-west-2
```

## Performance Optimization

### AppRunner Optimization
- Auto-scaling configuration
- Memory and CPU allocation
- Health check optimization
- Cold start minimization

### Application Optimization
- Database connection pooling
- Caching strategies
- Static asset optimization
- API response optimization

## Cost Optimization

### AWS Cost Management
- AppRunner instance sizing
- ECR lifecycle policies
- CloudWatch log retention
- Data transfer optimization

### Resource Monitoring
- Cost allocation tags
- Usage monitoring and alerting
- Resource cleanup automation
- Reserved capacity planning
