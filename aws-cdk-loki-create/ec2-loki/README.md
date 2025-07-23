# ec2-loki
Setting up a Loki server to collect logs from EC2 Instances and make them searchable. 

This code will create an EC2-Instance with Grafana and Loki

It will also have a script which can be run on EC2 Instance with logs that need to be uploaded.

### Project organization

#### directory structure


/infra
```
/infra/loki-cdk - root for AWS CDK v2 in python
``` 

/scripts
```commandline
/scripts/promtail - scripts for installing protail
```



#### CDK Grafana/Loki EC2 Instance
CDK code to se-tup an EC2 Instance with Grafana and Loki setup in the UserData section. The IP address is put into the CloudFormation Export section for a script installing Promtail on other EC2 Instance is setup. 


#### Promtail Install Script.
This script might be in either python or bash. It needs to read the URL for promtail from the AWS CloudFormation Stack Export section . It also needs to pickup a list of local directories to check for where to look for logs to export.

