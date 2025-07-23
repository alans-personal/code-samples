terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr     = var.vpc_cidr
  environment  = var.environment
  project      = var.project
  tags         = var.tags
}

# Cognito Module
module "cognito" {
  source = "./modules/cognito"

  environment = var.environment
  project     = var.project
  tags        = var.tags
}

# ECR Module
module "ecr" {
  source = "./modules/ecr"

  environment = var.environment
  project     = var.project
  tags        = var.tags
}

# AppRunner Module
module "apprunner" {
  source = "./modules/apprunner"
  
  environment = var.environment
  project     = var.project
  tags        = var.tags
  
  # ECR integration
  ecr_repository_url = module.ecr.repository_url
  ecr_repository_arn = module.ecr.repository_arn
  
  # AppRunner configuration
  service_name = "stripe-test-service"
  port         = 8000
  cpu          = "1024"
  memory       = "4096"
  
  # Environment variables - ADD ALL REQUIRED VARIABLES
  environment_variables = {
    ENVIRONMENT = var.environment
    PORT = "8000"
    AWS_REGION = var.aws_region
    COGNITO_USER_POOL_ID = "us-west-2_bF8V9arCh"
    COGNITO_CLIENT_ID = "73htfsj8cat2sipujjtvsnft3o"
    COGNITO_CLIENT_SECRET = "1krturp3uf3ml633oeqhoc7kbndf64p5dlou6j074bcl6opboc7u"
    STRIPE_PRICE_ID_TRIAL = "price_trial_default"
    STRIPE_PRICE_ID_BASIC = "price_basic_default"
    STRIPE_PRICE_ID_PREMIUM = "price_premium_default"
    STRIPE_SECRET_KEY = ""  # Add your actual key
    STRIPE_PUBLISHABLE_KEY = ""  # Add your actual key
    STRIPE_WEBHOOK_SECRET = ""  # Add your actual key
  }
} 