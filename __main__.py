import pulumi
import pulumi_aws as aws
import json

# Create a VPC
vpc = aws.ec2.Vpc("vllm-vpc",
    cidr_block="10.7.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": "vllm-vpc"
    }
)

# Create public subnet
public_subnet = aws.ec2.Subnet("public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.7.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,
    tags={
        "Name": "vllm-public-subnet"
    }
)

# Create private subnet
private_subnet = aws.ec2.Subnet("private-subnet",
    vpc_id=vpc.id,
    cidr_block="10.7.2.0/24",
    availability_zone="us-west-2b",
    tags={
        "Name": "vllm-private-subnet"
    }
)

# Create Internet Gateway
igw = aws.ec2.InternetGateway("vllm-igw",
    vpc_id=vpc.id,
    tags={
        "Name": "vllm-igw"
    }
)

# Create public route table
public_rt = aws.ec2.RouteTable("public-rt",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": igw.id
    }],
    tags={
        "Name": "vllm-public-rt"
    }
)

# Associate public subnet with public route table
public_rt_assoc = aws.ec2.RouteTableAssociation("public-rt-assoc",
    subnet_id=public_subnet.id,
    route_table_id=public_rt.id
)

ssm_role = aws.iam.Role("ssm-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Effect": "Allow",
        }]
    }),
    tags={
        "Name": "vllm-ssm-role"
    }
)

# Attach the SSM policy to the role
role_policy_attachment = aws.iam.RolePolicyAttachment("ssm-policy",
    role=ssm_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
)

# Create the instance profile
instance_profile = aws.iam.InstanceProfile("ssm-instance-profile",
    role=ssm_role.name,
    tags={
        "Name": "vllm-instance-profile"
    }
)

# Read the userdata script
with open("userdata.sh", "r") as f:
    userdata = f.read()

# Create EC2 instance in the public subnet
ec2_instance = aws.ec2.Instance("vllm-instance",
    instance_type="g5.xlarge",
    ami="ami-081f526a977142913",
    subnet_id=public_subnet.id,
    iam_instance_profile=instance_profile.name,
    user_data=userdata,
    root_block_device={
        "volume_size": 120,
        "volume_type": "gp3",
        "delete_on_termination": True,
    },
    tags={
        "Name": "vllm"
    }
)

# Export the important values
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("instance_id", ec2_instance.id)
pulumi.export("public_ip", ec2_instance.public_ip)
