locals {
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project
      ManagedBy   = "terraform"
    }
  )
}

resource "aws_cognito_user_pool" "main" {
  name = "${var.project}-${var.environment}-user-pool"

  username_attributes = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable            = true
    required           = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # Custom attribute for subscription plan
  schema {
    name                = "sub_plan"
    attribute_data_type = "String"
    mutable            = true
    required           = false

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }

  # Verification message template
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject = "MetroLunar Stripe Test Verification"
    email_message = "Your MetroLunar Stripe Test verification code is {####}"
    sms_message = "Your MetroLunar Stripe Test verification code is {####}"
  }

  tags = local.common_tags
}

resource "aws_cognito_user_pool_client" "main" {
  name = "${var.project}-${var.environment}-client"

  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = true

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]

  callback_urls = ["https://example.com/callback"]
  logout_urls   = ["https://example.com/logout"]

  supported_identity_providers = ["COGNITO"]

  token_validity_units {
    refresh_token = "days"
    access_token  = "hours"
    id_token      = "hours"
  }

  refresh_token_validity = 30
  access_token_validity  = 1
  id_token_validity     = 1
} 