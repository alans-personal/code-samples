#!/bin/bash

# Set variables
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="123456789012"   # TODO: Replace with actual account ID  
ECR_REPOSITORY="stripe-test"
IMAGE_TAG="latest"

# Stripe Price IDs for subscription plans
STRIPE_PRICE_ID_TRIAL="TBD"  # os.getenv("STRIPE_PRICE_ID_TRIAL", "price_trial_default")
STRIPE_PRICE_ID_BASIC="TBD"  # os.getenv("STRIPE_PRICE_ID_BASIC", "price_basic_default") 
STRIPE_PRICE_ID_PREMIUM="TBD"  # os.getenv("STRIPE_PRICE_ID_PREMIUM", "price_premium_default")

# Stripe API configuration
STRIPE_SECRET_KEY="TBD"  # os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY="TBD"  # os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET="TBD"  # os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Authenticate to ECR
echo "Authenticating to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build the image for x86 (linux/amd64) architecture
echo "Building Docker image for x86 (linux/amd64) architecture..."
docker build --platform linux/amd64 -t $ECR_REPOSITORY .

# Tag the image
echo "Tagging image for ECR..."
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Push to ECR
echo "Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

echo "Successfully pushed image to ECR!"