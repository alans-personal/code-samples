# Loki Grafana AWS CDK

A logging infrastructure project that sets up Grafana and Loki on EC2 instances for centralized log collection and visualization.

## Contact

**Email:** alan.snyder@gmail.com

## Project Overview

This project creates a centralized logging infrastructure using Grafana and Loki deployed on AWS EC2 instances. It provides a complete solution for collecting, storing, and visualizing logs from multiple EC2 instances across your infrastructure.

## Technologies

**Infrastructure-as-Code:** AWS CDK (Python)  
**Languages:** Python, Bash  
**Frameworks:** Grafana, Loki  
**AWS Services:** EC2, S3, DynamoDB, IAM, VPC, CloudFormation Exports

## AWS Services Used

- **EC2:** Hosts Grafana and Loki services
- **S3:** Storage backend for Loki log data
- **DynamoDB:** Index storage for Loki
- **IAM:** Security roles and permissions
- **VPC:** Network isolation and security
- **CloudFormation Exports:** Cross-stack resource sharing

## Project Structure

```
/infra
  /loki-cdk - AWS CDK v2 Python code for infrastructure
  /cloudwatch-2-loki - CloudWatch to Loki integration

/scripts
  /promtail - Promtail installation and configuration scripts
  /log-gen - Random log generation utilities
```

## Infrastructure Components

### CDK Stack (`loki-cdk/`)
The main infrastructure code that creates:
- EC2 instance with Grafana and Loki pre-configured
- S3 bucket for Loki storage
- DynamoDB table for Loki indexing
- Security groups with appropriate port access
- IAM roles with necessary permissions
- CloudFormation exports for cross-stack integration

### Key Features
- **Automated Setup:** UserData script automatically installs and configures Grafana and Loki
- **Security:** VPC isolation with controlled port access (SSH, HTTP, Grafana, Loki)
- **Scalability:** S3-backed storage for horizontal scaling
- **Integration:** CloudFormation exports enable other stacks to discover the Loki endpoint

## Scripts and Utilities

### Deployment Scripts

#### **CDK Deployment**
```bash
cd infra/loki-cdk
pip install -r requirements.txt
cdk deploy
```

#### **Promtail Installation** (`scripts/promtail/`)
Scripts for installing and configuring Promtail on EC2 instances:
- **`install_promtail.py`:** Automated Promtail installation
- Reads Loki endpoint from CloudFormation exports
- Configures log directory monitoring
- Sets up systemd service for automatic startup

### Log Generation Utilities

#### **Random Log Generator** (`scripts/log-gen/`)
- **`rand_log_gen.py`:** Generates sample log data for testing
- Creates realistic log patterns
- Useful for testing Grafana dashboards and Loki queries

## Code Locations

### Infrastructure Code
- **Main Stack:** `infra/loki-cdk/loki_cdk/loki_cdk_stack.py`
- **CDK App:** `infra/loki-cdk/app.py`
- **User Data Script:** `infra/loki-cdk/loki_cdk/user_data_loki_ec2_inst.sh`
- **Loki Config:** `infra/loki-cdk/loki_cdk/loki-s3-storage-config.yaml`

### Scripts
- **Promtail Installation:** `scripts/promtail/install_promtail.py`
- **Log Generation:** `scripts/log-gen/rand_log_gen.py`

## Deployment Process

1. **Deploy Infrastructure:**
   ```bash
   cd infra/loki-cdk
   cdk deploy
   ```

2. **Install Promtail on Source Instances:**
   ```bash
   # Use the provided script to install Promtail
   python scripts/promtail/install_promtail.py
   ```

3. **Configure Log Sources:**
   - Update Promtail configuration with log directories
   - Restart Promtail service

4. **Access Grafana:**
   - Navigate to `http://<EC2-IP>:3000`
   - Default credentials are configured in UserData script

## Configuration

### Loki Configuration
The Loki configuration is stored in `loki-s3-storage-config.yaml` and includes:
- S3 storage backend configuration
- DynamoDB index configuration
- Retention policies
- Query optimization settings

### Grafana Configuration
Grafana is pre-configured with:
- Loki data source
- Sample dashboards
- User authentication setup

## Monitoring and Maintenance

### Health Checks
- Grafana health endpoint: `http://<EC2-IP>:3000/api/health`
- Loki health endpoint: `http://<EC2-IP>:3100/ready`

### Log Rotation
- Loki automatically manages log retention based on configuration
- S3 lifecycle policies can be configured for cost optimization

### Scaling
- Add additional EC2 instances behind a load balancer
- Configure Loki clustering for high availability
- Use S3 cross-region replication for disaster recovery

## Security Considerations

- All services run within VPC with controlled access
- IAM roles follow least privilege principle
- SSL/TLS encryption for data in transit
- S3 bucket encryption for data at rest
- Regular security updates via UserData script

## Troubleshooting

### Common Issues
1. **Promtail Connection Issues:** Verify CloudFormation exports and network connectivity
2. **Storage Issues:** Check S3 bucket permissions and DynamoDB table access
3. **Performance Issues:** Monitor EC2 instance metrics and Loki query performance

### Debug Commands
```bash
# Check Loki status
curl http://<EC2-IP>:3100/ready

# Check Grafana status
curl http://<EC2-IP>:3000/api/health

# View Loki logs
sudo journalctl -u loki -f

# View Promtail logs
sudo journalctl -u promtail -f
```

