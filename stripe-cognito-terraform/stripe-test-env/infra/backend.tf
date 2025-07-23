terraform {
  backend "s3" {
    bucket         = "terraform-state-metrolunar-123456789012"  # replace with real AWS Account ID
    key            = "envs/dev/terraform.tfstate"  # choose a logical path
    region         = "us-west-2"
    dynamodb_table = "terraform-locks-metrolunar"
    encrypt        = true
  }
} 