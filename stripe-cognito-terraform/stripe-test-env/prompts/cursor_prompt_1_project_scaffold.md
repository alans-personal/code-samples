# Cursor Project Scaffold Prompt

This prompt can be used in the Cursor IDE to scaffold a full-stack project with AWS infrastructure, FastAPI backend, optional NiceGUI frontend, and `pytest` testing. The directory structure and behavior are explicitly defined below.

---

## Project Structure and Rules

### /infra
- Contains all **Terraform** code.
- Manages infrastructure in **AWS**.
- Default AWS region: `us-west-2`.
- AWS Account ID for deployment: **280415439178**.
- Resources like Cognito, ECR, AppRunner, VPC, etc., will be defined here.
- Organized into modules: `/infra/modules/` for reusable components.

---

### /src
- Contains **Python 3** application source code.
- Uses **FastAPI** for the backend.
- Uses **NiceGUI** for frontend features when needed.
- The application will be containerized with **Docker** and deployed to **AWS AppRunner**.
- Main application file: `src/main.py`.

---

### /test
- Contains all **testing code**.
- Uses the **`pytest`** framework.
- Include support for **`httpx.AsyncClient`** for integration testing with FastAPI.
- Test files should follow the pattern `test_*.py`.

---

### /prompts
- Contains **Cursor prompt files** used to document AI interactions and project automation steps.
- This folder is **manually maintained**.
- **Do not generate or modify files** in `/prompts` via Cursor.

---

### Root Level Files
- `Dockerfile`: Container configuration for the application.
- `requirements.txt`: Python dependencies.
- `build-and-push.sh`: Script to build and push Docker images to ECR.
- `test-local.sh`: Script to test the application locally.
- `test-local-cleanup.sh`: Script to clean up local test resources.
- `README.md`: Project documentation and setup instructions.

---

### Deployment Architecture
- **Container Registry**: AWS ECR for storing Docker images.
- **Compute Service**: AWS AppRunner for running the containerized application.
- **Authentication**: AWS Cognito for user management.
- **Networking**: Custom VPC with public and private subnets.
- **Monitoring**: CloudWatch for logs and metrics.

---
