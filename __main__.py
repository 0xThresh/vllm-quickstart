import pulumi
import pulumi_aws as aws
import json

# Get the Pulumi config to access DataDog API key and HF token (if applicable)
config = pulumi.Config()
datadog_api_key = config.require("DataDogAPIKey")
datadog_site = config.require("DataDogSite")
hf_token = config.require("HFToken")
model = config.require("Model")

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

# Create EC2 instance in the public subnet
ec2_instance = aws.ec2.Instance("vllm-instance",
    instance_type="g5.xlarge",
    ami="ami-081f526a977142913",
    subnet_id=public_subnet.id,
    iam_instance_profile=instance_profile.name,
    user_data=f"""#!/bin/bash
# Get secrets, sourced from Pulumi
export DD_API_KEY={datadog_api_key}
export DD_SITE={datadog_site}
export HF_TOKEN={hf_token}

# Install Conda
mkdir -p /usr/lib/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-py310_24.11.1-0-Linux-x86_64.sh -O /usr/lib/miniconda3/miniconda.sh
bash /usr/lib/miniconda3/miniconda.sh -b -u -p /usr/lib/miniconda3/
rm /usr/lib/miniconda3/miniconda.sh

# Set up vLLM
/usr/lib/miniconda3/bin/conda create -n vllm python=3.10 -y
/usr/lib/miniconda3/bin/conda activate vllm
pip install vllm
# Set the HF_TOKEN value if it's passed into userdata to allow vLLM to pull gated models
if [ ! -z "$HF_TOKEN" ]; then
    export HF_TOKEN=$HF_TOKEN
fi
vllm serve {model} &

# Set up DataDog agent 
DD_API_KEY=$DD_API_KEY \
DD_SITE=$DD_SITE \
bash -c "$(curl -L https://install.datadoghq.com/scripts/install_script_agent7.sh)"

# Enable vLLM DataDog integration
cat << EOF > /etc/datadog-agent/conf.d/vllm.d/conf.yaml
init_config:
    service: vllm

instances:
  - openmetrics_endpoint: http://localhost:8000/metrics
    enable_health_service_check: true
EOF
""",
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
