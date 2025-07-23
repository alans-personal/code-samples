Please review the Terraform code in `src/modules/cognito/main.tf`.

The goal is to ensure it properly defines an AWS Cognito UserPool that:
- Allows new users to create an account using their **email address**
- Enforces a secure **password-based signup flow**
- Ensures email is used as the **username attribute**
- Enforces appropriate **password policy**
- Has the correct schema for **email**
- Creates a **User Pool Client** that supports `ALLOW_USER_PASSWORD_AUTH` in addition to `ALLOW_USER_SRP_AUTH` and `ALLOW_REFRESH_TOKEN_AUTH`, to support email+password login
- Uses `"COGNITO"` as the supported identity provider
- Keeps appropriate defaults for token validity and client settings
- Retains all tagging and naming patterns using project/environment
- Preserve existing environment-specific configurations

If any of these behaviors are missing or misconfigured, please update the Terraform accordingly while preserving existing variable usage and tag structure.

Do not change unrelated settings. Leave callback and logout URLs unchanged.