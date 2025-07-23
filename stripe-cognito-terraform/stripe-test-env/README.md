# Test project Sign-up flow and Stripe API payments.

This code is intended to run in the "MetroLunar" AWS account (280...178). 
The UI is intended to test sign-up into Cognito workflow and Stripe API.

This is a full-stack application built with FastAPI, NiceGUI, and AWS infrastructure. The project follows a well-defined structure for maintainability and scalability.

## Project Structure

- `/infra`: Terraform code for AWS infrastructure
- `/src`: Python application source code (FastAPI + NiceGUI)
- `/test`: Pytest test suite
- `/prompts`: Project documentation and AI interaction prompts

## Prerequisites

- Python 3.x
- Terraform
- AWS CLI configured with appropriate credentials
- Docker (for containerization)

## Setup

1. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials:
```bash
aws configure
  -or-
export AWS_PROFILE=metrolunar
```

4. Initialize Terraform:
```bash
cd infra
terraform init
```

## Development

1. Start the development server:
```bash
python src/main.py
```

2. Run tests:
```bash
pytest
```

## Containerization and Deployment

### Local Docker Testing

Test the Docker image locally before deploying to AWS:

```bash
# Test the Docker image locally
./test-local.sh

# Clean up Docker containers and images
./test-local-cleanup.sh
```

The `test-local.sh` script will:
- Build the Docker image
- Run the container on port 8000
- Test the health and root endpoints
- Open the application in your browser
- Display container logs

### Building and Pushing Docker Image to ECR

1. **Authenticate Docker to ECR:**
```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com
```

2. **Build the Docker image:**
```bash
docker build -t stripe-test .
```

3. **Tag the image for ECR:**
```bash
docker tag stripe-test:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:latest
```

4. **Push the image to ECR:**
```bash
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:latest
```

### Automated Deployment Script

Create a deployment script for convenience:

```bash
#!/bin/bash

# Set variables
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="<AWS_ACCOUNT_ID>"
ECR_REPOSITORY="stripe-test"
IMAGE_TAG="latest"

# Authenticate to ECR
echo "Authenticating to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build the image
echo "Building Docker image..."
docker build -t $ECR_REPOSITORY .

# Tag the image
echo "Tagging image for ECR..."
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Push to ECR
echo "Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

echo "Successfully pushed image to ECR!"
```

### Version Tagging

For production deployments, use version tags:

```bash
# Tag with version number
docker tag stripe-test:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:v1.0.0
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:v1.0.0

# Tag with commit hash
docker tag stripe-test:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:$(git rev-parse --short HEAD)
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/stripe-test:$(git rev-parse --short HEAD)
```

### Verify ECR Push

After pushing, verify the image is in ECR:

```bash
aws ecr describe-images --repository-name stripe-test --region us-west-2
```

### Quick Deployment

Run the deployment script from the project root:

```bash
./build-and-push.sh
```

This script will authenticate to ECR, build the Docker image, tag it, and push it to the repository.

## Infrastructure

The infrastructure is managed through Terraform in the `/infra` directory. The default AWS region is `us-west-2`.

The infrastructure includes:
- **VPC** with public and private subnets
- **ECR** repository for container images
- **AppRunner** service for container deployment
- **Cognito** for user authentication

## Testing

Tests are written using pytest and include integration tests with FastAPI using httpx.AsyncClient.

## License

This code is proprietary and not licensed for public or open-source use.
