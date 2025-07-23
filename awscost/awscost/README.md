# AwsCost Project

This project helps give insight into how to reduce the AWS Bill, by using resources more efficiently from a cost stand perspective. 

It will be compose of several sub-projects:

**A)** Store hourly usage data of AWS Resource types that can be bought with Reserved capacity more cheaply.  

**B)** Send reports to managers and engineers detailing costs for their AWS accounts, total AWS resource usage, Spend_Category tag coverage, and eventually cost estimates for micro-services.

**C)** Attempt to track micro-service costs (which will require Docker container use logging) to give good cost estimates of individual micro-service that engineers can use for optimizing (cost) for their services

**D)** Cost Panda with Jupyter Notebook.  Load billing file into format for quick data analysis when needed, so they can be turned into code to generate specific reports.


## Hourly / Daily Use Tracking

A CRON-based lambda function records once per hour or day the usage of the following resource types accross all accounts and stores them per AWS account and aggregated Roku-wide. 

##### AWS Resources Tracked
 # | AWS Resource | Tracking frequency | Key prefix
---:| --- |:---:| ---
1 | EC2 | hourly | ec2 & ec2os
2 | RDS | hourly | rds
3 | DynamoDB Provisioned Capacity | hourly | dynamodb
4 | Elasticache (Redis clusters) | hourly | elasticache
5 | Elastic Search Service | daily | es
6 | Redshit Nodes | daily | redshift

Hourly usage data is stored in the AWSCost DynamoDB table with the following keys. 

##### AWSCost DynamoDB table keys (with example AWS account ID)
Key format | Example | Description
:--- :|:---:|:---
ec2:asnyder:{region} | ec2:asnyder:us-east-1 | EC2 Instance usage by Availability Zones - asnyder wide
ec2:{aws-account}:{region} | ec2:<AWS_ACCOUNT_ID>:us-west-2 | EC2 Instance usage by Availability Zones per AWS account
ec2os:asnyder:{region} | ec2os:asnyder:us-east-1 | EC2 Instance usage by OS-type - asnyder wide
ec2os:{aws-account}:{region} | ec2os:<AWS_ACCOUNT_ID>:us-west-2 | EC2 Instance usage by OS-type per AWS account
rds:asnyder:{region} | rds:asnyder:us-east-1 | RDS database nodes - asnyder wide
rds:{aws-account}:{region} | rds:<AWS_ACCOUNT_ID>:us-west-2 | RDS database nodes per AWS account
dynamodb:asnyder:{region} | dynamodb:asnyder:us-east-1 | DynamoDB Provisioned Capacity - asnyder wide
dynamodb:{aws-account}:{region} | dynamodb:<AWS_ACCOUNT_ID>:us-west-2 | DynamoDB Provisioned Capacity per AWS account
elasticache:asnyder:{region} | elasticache:asnyder:us-east-1 | Redis/Memcache Nodes types - asnyder wide
elasticache:{aws-account}:{region} | elasticache:<AWS_ACCOUNT_ID>:us-west-2 | Redis/Memcache Nodes types per AWS account
es:asnyder:{region} | es:asnyder:us-east-1 | Elastic Search Service Node - asnyder wide
es:{aws-account}:{region} | es:<AWS_ACCOUNT_ID>:us-west-2 | Elastic Search Service Node per AWS account
redshift:asnyder:{region} | redshift:asnyder:us-east-1 | Redshift Node types - asnyder-wide
redshift:{aws-account}:{region} | redshift:<AWS_ACCOUNT_ID>:us-west-2 | Redshift Node types per AWS account
ri-ec2:asnyder:{region} | ri-ec2:asnyder:us-east-1 | EC2 Reserved Instances - asnyder-wide
ri-rds:asnyder:{region} | ri-rd:asnyder:us-east-1 | RDS Reserved Instance - asnyder-wide
ri-elasticache:asnyder:{region} | ri-rd:asnyder:us-east-1 | Elasticacche Reserved Nodes - asnyder-wide
ri-redshift:asnyder:{region} | ri-rd:asnyder:us-east-1 | RedShift Reserved Instance - asnyder-wide

NOTE: Currently missing are ElasticSearch Service and DynamoDB

NOTE: Amazon does not currently seem to have a boto3 API for getting the "Reserved Capacity" per AWS account.
So an alternate way will be needed to track it.
This alternative way is AWS Cost Explorer API.  

##### AWS Reserved Instance/Capacity purchasing options

Type | Key prefix | value format | Comment
:---:|:---:|:---:|:---
EC2 | ec2 | c4.large:us-west-2a | includes AZ. (Not needed, Need OS instead)
EC2 | ec2os | linux-c4.large | Include estimate of OS based on AMI id. Excludes AZ summary. 
EC2 RIs | ri-ec2 | linux-t2.small | includes OS (linix, RHEL, Windows)
RDS | rds | db.r4.large:aurora-mysql | needs DB engine
Elasticache | elasticache | cache.r4.large | Need to look RI purchase options
Elastic Search Service | es | m4.large.elasticsearch | Need to look RI purchase options
Redshift | redshift | dc2.8xlarge | RI purchase options...
DynamoDB | dynamodb | write_capacity | All include counts of read_capacity, write_capacity and table_count 
CE Coverage* | ce-cov | m4.large | Cost Explorer Coverage report. 
CE Utilization* | ce-util | m4.large | Cost Explorer Utilization report
CE Recommend 7 Day* | ce-rec-7 | m4.large | Cost Explorer Recommendation Report 7 Days lookback
CE Recommend 60 Day* | ce-rec-60 | m4.large | Cost Explorer Recommendation Report 60 Day lookback

* Index tht needs to be added.

###### ToDos

 - Make sure the "ri-*" pages in the Excel file display just daily data.
 - Improve AMI detection. 
    - Code AMI IDs to OS type associations with AWSCostMap table. (until a better way is found)  
 - Take Excel file results and turn into plots with pandas, which are stored in S3.  
 - Extend look-back to 4 weeks on Jan. 20th.
 - Put Cost Explorer CVS file into S3, or make CE call and publish  CSV file. 
 - Store CE Utility, Coverage and Recommendation reports in DynamoDB table, and CSV file in S3.
 - Proto - Making graphs with Plot.ly(or other options) that are stored in account.
    - If works, make stack plots for (Accounts+AWS Account) for dynamo, ec2, rds, es, elasticache, redshift
 - Make a Slack command to get charts and graphs and reports.
    - JIRA# ?
    - Move "untagged" slack command into this command. 
 - Investigate Budgets API for alerts to groups.
    - JIRA# ?
 - Load the AWS Cost CVS file into Jupyter Notebook, create code for different report types
 - Investigate creating a Jupyter interface for groups to create reports.
 

###### Look into following bugs.
 - EC2 scan data in us-east-1 is missing from 1/6 at 10 AM.  (Verify is isn't hitting a lambda function limit) 
 - P95 Dynamo * tabs missing "read_capacity" column.
 - Elasticache us-east-1 data looks bad after 2018-12-3, ... check
 - Check if elasticache east and west regions swapped.
 
###### AWSCost Data collection history. 
 - RDS data collection started Nov. 16th, 7 AM
 - Elastic Search Service data collection started Nov. 16th, 1 PM
 - Redshift data collection started Nov. 16th, 3 PM
 - DynamoDB data collection started Nov. 16th, 6 PM
 - All resource types miss data collection Nov. 27th evening until Nov. 28th morning.
 - Elasticache (Redis) data collection started Nov. 28th 7 PM
 - Data collection for Redshift and Elastic Search became once per day instead of hourly staring Nov. 27 5 PM.
 - All Redshift and Elastic Search Service data is verified clean starting Dec. 3rd. (before could be clean too, but not verified)
 - Some limited lambda error occurred from Dec. 3rd until Dec. 5th but data was repaired.
 - EC2 data collection by AZ started Dec. 5th, 6 PM
 - EC2 data collection by OS started Dec. 19, 9 PM
 - EC2 data collection takes spot instance into account starting Dec. 20, 8 AM.
 - RDS data collection. Added multi_az-  in front of node types with multi-AZ RDS nodes. Dec. 21, 2 PM.
 - Data collection down for all types between Friday noon Jan. 18, 2019 and Monday midnight Jan. 21.
 - Added PayQA, PayStg and PayProd AWS accounts to the scans at 7 PM Jan. 29, 2019 (Tuesday) 
 - Added NPIAudio to the scans at 7 PM Jan. 30, 2019 (Wednesday)

### EC2 purchase options ...
[AWS EC2 Reserved Instance Purchase Page](https://aws.amazon.com/ec2/pricing/reserved-instances/)

##### Notes
1. Standard discounts larger than Convertible, but we are doing convertible for the flexibility.
2. Purchasing options have following categories.
 
Category | Options... | Description | Comment
:--- | --- |:--- |:---
Platform| Linux, RHEL, Windows| OS | This is hard to determine
Tenancy| Default, Dedicated | use default | Negligible dedicated 
Offering Class | Convertible, Standard | Using convertible | 
Instance Type | t2.small, m3.large, ... | Instance families | 
Term | 1 year, 3 year | Doing all 1 year | How long
Payment | All, Partial, No Upfront | ? all upfront | Verify the term


### RDS purchase options ...
[AWS RDS Reserved Instance Purchase Page](https://aws.amazon.com/rds/reserved-instances/)

##### Notes
1. Region, DB Engine, DB Instance Class, Deployment Type and term length must be chosen at purchase, and cannot be changed later.
2. You can purchase up to 40 Reserved Instances. If you need additional Reserved Instances, complete the form found here.
3. Reserved Instances may not be transferred, sold, or cancelled and the one-time fee is non-refundable.

##### Some example DB Instance Classes. 

- db.m4.2xlarge MySQL RI applys to 2 db.m4.xlarge MySQL
- Single AZ vs. Multi AZ. (50% covered) 

## Reports stored in S3 bucket AWSCost

AwsRIUsageReport
Roku level reports.  (ToDo: add more detail here.)
 
Should have pages for all regions and all AWS Resource types with columns for 
each Reserved type that can be purchases. 

Also each page include summary types, with P95 stats for the purchase options.
