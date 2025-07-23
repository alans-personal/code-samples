from aws_cdk import (
    CfnOutput,
    Stack,
)
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class LokiCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Read the VPC_ID from the CFn Export section.
        vpc_id = aws_cdk.Fn.import_value("vpc_id")  # vpc-0c15d73d7a3968763
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)

        # Create S3 bucket for Loki storage
        loki_s3_bucket_name = aws_cdk.Fn.import_value("loki_s3_bucket_name")  # loki-s3-storage-test
        bucket = s3.Bucket(self, "loki-s3-storage-test",
                           bucket_name=loki_s3_bucket_name)

        # Create a Security Group
        security_group = ec2.SecurityGroup(
            self, 'GrafanaPublicEc2SecurityGroup',
            vpc=vpc,
            allow_all_outbound=True  # Allow outbound traffic
        )
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), 'SSH access from anywhere')
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), 'HTTP access from anywhere')
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(3000), 'Grafana port access from anywhere')
        security_group.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc_cidr_block), ec2.Port.tcp(3100), 'Loki port access from VPC only')
        # Does the UI need loki port 3100 open?

        # Grant EC2 and S3 permissions to this instance.
        role = iam.Role(self, "GrafanaInstanceRole",
                        assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                        description="Role for Grafana EC2 Instance, grants EC2, S3 and DynamoDB access"
                        )
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))

        # Create a key pair for SSH access
        key_pair = ec2.KeyPair.from_key_pair_name(self, "FinTechUSWest2KeyPair", key_pair_name="fintech-us-west-2-key")

        machine_image = ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)

        # define what is needed like UserData etc.
        with open("loki_cdk/user_data_loki_ec2_inst.sh") as user_data_file:
            user_data = user_data_file.read()

        # create the EC2-Instance
        instance = ec2.Instance(
            self, 'GrafanaLokiServer',
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),  # T2 Micro instance
            machine_image=machine_image,
            security_group=security_group,
            key_pair=key_pair,
            role=role,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            user_data=ec2.UserData.custom(user_data)
        )

        # get the IP address of the EC2 Instance to put as output needed for promtail script.
        CfnOutput(self, "loki_push_logs_url",
                  value=f"{instance.instance_private_ip}:3100",
                  export_name="loki-push-logs-url")

        CfnOutput(self, "loki-s3-bucket",
                  export_name="loki-s3-bucket",
                  value=bucket.bucket_name)

        CfnOutput(self, "loki-index-dynamo-table",
                  export_name="loki-index-dynamo-table",
                  value=table.table_name)
