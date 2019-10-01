Lambda@Edge + ALB demo
======================

Prerequisites
-------------
To deploy this demonstration, you will need:

- Access to an AWS account and the ability to create resources in the account
- Access to a domain name, specifically the ability to create an `IN NS` delegation record
- A keypair in the region you want to deploy the `demo.yaml` stack in
- Access to one S3 bucket in `us-east-1` and one S3 bucket in the region the `demo.yaml` stack will be deployed
- (Optional) AWS CLI. Stacks can also be created from the AWS Console

To create a keypair using the AWS CLI:
```
aws ec2 create-key-pair --key-name [name] --region [region]
```

Description
-----------
This demonstration is made of two CloudFormation stacks, `demo.yaml` and `cloudfront.yaml`. 

#### Bill of materials
- `demo.yaml`:
  - 1 network nested stack (`vpc.yaml`)
    - 1 VPC
    - 2 private subnets
    - 2 public subnets
    - 1 Internet Gateway
    - 1 NAT Gateway
  - 4 applications nested stacks (`app.yaml`)
    - 1 autoscaling group (`min=2, max=2`)
    - 1 target group 
    - 2 instances
    - 1 security group for the instances
    - 1 instance profile and 1 role for the instances
  - 1 load balancer nested stack (`lb.yaml`)
    - 1 ALB with an HTTPS listener
    - 1 DNS record for the ALB
    - 4 rules (one per application). 2 rules are based on paths, 2 rules are based on headers.
    - 1 security group 
    - 1 ACM certificate for the ALB
  - A Route 53 zone
- `cloudfront.yaml`:
  - 1 CloudFront distribution
  - 1 DNS record for the distribution
  - 1 ACM certificate for the distribution 
  - 1 Lambda function 
  
Deployment instructions
-----------------------
Both stacks need to be packaged using `aws cloudformation package` before they are deployed.
This will upload the nested dependencies to S3 and create a modified template which 
references the S3 locations.

##### Applications and load balancer
The `demo.yaml` stack can be deployed in any region. 

###### Parameters
- `CreateHostedZone`: create the hosted zone for `BaseDomainName` (`true` or `false`). Defaults to `true`
- `KeyPair`: the name of a key pair in the region the stack is deployed 
- `BaseDomainName`: a domain you control, preferably a third level domain (e.g.: `demo.redhead.cloud`)
- `LoadBalancerDomainName`: the FQDN of the load balancer. The FQDN **must** be part of the
  hierarchy of `BaseDomainName`
- `CIDR`: CIDR of the VPC to create for this demo.

###### Commands
When creating the stack for the first time, login to the AWS Console, navigate to ACM and
follow the instructions to create the validation record for the ALB domain name certificate.

```
aws cloudformation package --template-file demo.yaml \
    --s3-bucket [bucket] \
    --output-template-file /tmp/tmp1.yaml
    
aws cloudformation deploy --template-file /tmp/tmp1.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --stack-name [stack-name] \
    --parameter-overrides \
        "KeyPair=[key-pair]" \
        "BaseDomainName=[domain-name]" \
        "LoadBalancerDomainName=[lb].[base-domain-name]" \
        "CIDR=[cidr]" \
    --region [region]
```

##### CloudFront distribution
The `cloudfront.yaml` stack can **only** be deployed in the `us-east-1` region. 
###### Parameters 
- `BaseDomainName`: a domain you control, preferably a third level domain (e.g.: `demo.redhead.cloud`)
- `LoadBalancerDomainName`: the FQDN of the load balancer. This parameter must match the parameter
  of the same name in the `demo.yaml` stack.
- `DistributionDomainName`: the FQDN of the CloudFront distribution. The FQDN **must** be
  part of the hierarchy of `BaseDomainName`

###### Commands
Creating this stack may take up to 2 hours. Updates may take up to 30 minutes. When creating
the stack for the first time, login to the AWS Console, navigate to ACM and follow the
instructions to create the validation record for the CloudFront distribution domain name
certificate.

```
aws cloudformation package --template-file cloudfront.yaml \
    --s3-bucket [bucket-us-east-1] \
    --region us-east-1 \
    --output-template-file /tmp/tmp2.yaml

aws cloudformation deploy --template-file /tmp/tmp2.yaml \
    --stack-name cf-lambda-demo \
    --parameter-overrides \
        "BaseDomainName=[domain-name]" \
        "DistributionDomainName=[distribution].[domain-name]" \
        "LoadBalancerDomainName=[lb].[domain-name]" \
    --region us-east-1 \
    --capabilities CAPABILITY_NAMED_IAM
```

Testing
-------
Once both stacks are deployed, navigate to the following URLs to test the rules are 
functioning as intended:

- Application A (path-based rule)
  - `/a`
  - `/a/roger`
- Application B (path-based rule)
  - `/b`
  - `/b/tomato`
- Application C (regular expression + header)
  - `/c`
  - `/c/123`
- Application D (regular expression + header)
  - `/d`
  - `/d/123`
    