#!/usr/bin/env python3
"""Utility for provisioning an EC2 instance that hosts a simple Apache page.

The instance is created as a t4g.micro with Amazon Linux 2023 (arm64).  A security
 group is created/opened to expose TCP port 5001 to the internet while limiting
 SSH access to the caller's current public IP address.  The boot-time user data
 installs Apache, reconfigures it to listen on port 5001, and publishes an HTML
 page that includes the instance type and the public URL where the server can be
 reached.

Example usage::

    python AWS/00_create_machine.py --key-name my-ec2-key

The script will:
  * discover (or optionally create) the security group
  * look up the latest Amazon Linux 2023 ARM64 AMI via the AWS Systems Manager
    public parameter store
  * launch an EC2 t4g.micro instance with the supplied key pair
  * wait for the instance to become ready and display connection information

AWS credentials and default region must be configured in your environment.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.exceptions import ClientError


AWS_KEY_PATH = "/Users/rick/Desktop/stuff/keys/aws_key4.pem"
DEFAULT_KEY_NAME = "aws_key4"  # Default key name matching the PEM file
DEFAULT_SECURITY_GROUP_NAME = "apache-5001-sg"
DEFAULT_REGION = "us-east-1"  # Default AWS region

# AWS credentials from environment variables
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SSM_AMI_PARAMETER = (
    "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
)
USER_DATA_TEMPLATE = """#!/bin/bash
set -eux

yum update -y
yum install -y httpd

# Configure Apache to listen on port 5001 instead of 80.
sed -i 's/^Listen 80/Listen 5001/' /etc/httpd/conf/httpd.conf

# Get actual values from metadata service with proper error handling
INSTANCE_TYPE=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-type 2>/dev/null || echo "t4g.micro")
PUBLIC_IP=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
PUBLIC_HOST=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null || echo "$PUBLIC_IP")

# If we still don't have a public host, use the IP we know from the script output
if [ -z "$PUBLIC_HOST" ] || [ "$PUBLIC_HOST" = "" ]; then
    PUBLIC_HOST="YOUR_INSTANCE_IP"
fi

# Create the final HTML page
cat <<EOF_HTML >/var/www/html/index.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Trading AI EC2 demo</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 3rem; background: #f7f7f7; }
    main { background: white; padding: 2rem; border-radius: 0.75rem; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
    h1 { color: #20253f; }
    p { font-size: 1.1rem; }
    code { font-weight: 600; }
  </style>
</head>
<body>
  <main>
    <h1>Trading AI EC2 Sample</h1>
    <p>Instance type: <code>$INSTANCE_TYPE</code></p>
    <p>Public endpoint: <a href="http://$PUBLIC_HOST:5001/">http://$PUBLIC_HOST:5001/</a></p>
    <p>Hello from your brand-new Apache server on AWS!</p>
  </main>
</body>
</html>
EOF_HTML

systemctl enable httpd
systemctl restart httpd
"""


@dataclass
class SecurityGroupResult:
    group_id: str
    name: str
    created: bool


def main(argv: Optional[list[str]] = None) -> int:
    # All configuration hardcoded like the EC2 GitHub update script
    key_name = DEFAULT_KEY_NAME
    region = DEFAULT_REGION
    security_group_name = DEFAULT_SECURITY_GROUP_NAME
    skip_key_check = True  # Always skip since we have the PEM file
    create_key = False  # Don't create new keys

    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=region
    )
    ec2_client = session.client("ec2")
    ec2_resource = session.resource("ec2")
    ssm_client = session.client("ssm")

    public_ip = discover_public_ip()
    ssh_cidr = f"{public_ip}/32"
    print(f"Detected public IP: {public_ip} (SSH access will be restricted to this address)")

    ensure_key_pair(
        ec2_client,
        key_name=key_name,
        create_if_missing=create_key,
        skip_check=skip_key_check,
        key_path=None,
    )

    sg_result = ensure_security_group(
        ec2_client,
        group_name=security_group_name,
        ip_cidr=ssh_cidr,
    )
    status = "created" if sg_result.created else "using existing"
    print(f"Security group {sg_result.name} ({sg_result.group_id}) ready ({status}).")

    ami_id = fetch_latest_ami_id(ssm_client)
    print(f"Using AMI {ami_id} (Amazon Linux 2023 arm64).")

    instance = launch_instance(
        ec2_resource,
        ami_id=ami_id,
        key_name=key_name,
        security_group_id=sg_result.group_id,
        public_ip="YOUR_INSTANCE_IP",  # Placeholder, will be updated after launch
    )
    print(f"Launched instance {instance.id}; waiting for it to become ready...")

    instance = wait_for_instance(instance)
    dns = instance.public_dns_name or instance.public_ip_address
    url = f"http://{dns}:5001/"
    
    # Wait for user data script to complete and update the HTML page
    print("Waiting for user data script to complete...")
    time.sleep(30)  # Wait for user data script to finish
    
    print("Updating HTML page with actual public IP...")
    update_script = f"""
    # Wait for the HTML file to exist and then update it
    for i in {{1..10}}; do
        if [ -f /var/www/html/index.html ]; then
            sudo sed -i 's/YOUR_INSTANCE_IP/{dns}/g' /var/www/html/index.html
            sudo sed -i 's/<code><\\/code>/<code>t4g.micro<\\/code>/g' /var/www/html/index.html
            echo "HTML page updated successfully"
            break
        fi
        echo "Waiting for HTML file... attempt $i/10"
        sleep 5
    done
    """
    subprocess.run([
        "ssh", "-i", AWS_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"ec2-user@{dns}",
        update_script
    ], check=False)
    print("Instance is ready!")
    print(f"  Instance ID: { instance.id}")
    print(f"  Instance type: {instance.instance_type}")
    print(f"  Public IPv4: {instance.public_ip_address}")
    print(f"  Public DNS: {dns}")
    print(f"  Apache URL: {url}")

    print("\nYou can connect via SSH using:\n")
    print(f"  ssh -i {AWS_KEY_PATH} ec2-user@{dns}")
    return 0


def discover_public_ip() -> str:
    """Return the caller's current public IPv4 address."""

    services = (
        "https://checkip.amazonaws.com",
        "https://api.ipify.org",
    )
    for service in services:
        try:
            with urllib.request.urlopen(service, timeout=10) as response:
                return response.read().decode("utf-8").strip()
        except (urllib.error.URLError, TimeoutError):
            continue
    raise RuntimeError(
        "Unable to determine the current public IP address; please check your network connection."
    )


def ensure_security_group(
    ec2_client, *, group_name: str, ip_cidr: str
) -> SecurityGroupResult:
    """Create or update the security group and return its identifier."""

    # Find the default VPC to attach the security group.
    vpcs = ec2_client.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    if not vpcs["Vpcs"]:
        raise RuntimeError("No default VPC found; please specify networking details manually.")
    vpc_id = vpcs["Vpcs"][0]["VpcId"]

    try:
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description="Allow SSH from client IP and expose Apache on port 5001",
            VpcId=vpc_id,
        )
        group_id = response["GroupId"]
        created = True
    except ClientError as exc:  # Security group may already exist.
        error_code = exc.response["Error"].get("Code")
        if error_code != "InvalidGroup.Duplicate":
            raise
        # Look up the existing security group.
        groups = ec2_client.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [group_name]}, {"Name": "vpc-id", "Values": [vpc_id]}]
        )["SecurityGroups"]
        if not groups:
            raise RuntimeError("Security group reported as duplicate but could not be found.")
        group_id = groups[0]["GroupId"]
        created = False

    # Configure ingress rules: 5001 from anywhere, 22 from specific IP.
    permissions = [
        {
            "IpProtocol": "tcp",
            "FromPort": 5001,
            "ToPort": 5001,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "Allow HTTP on 5001"}],
        },
        {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [
                {"CidrIp": ip_cidr, "Description": "SSH access from current public IP"}
            ],
        },
    ]

    try:
        ec2_client.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=permissions,
        )
    except ClientError as exc:
        error_code = exc.response["Error"].get("Code")
        if error_code != "InvalidPermission.Duplicate":
            raise
        # If duplicates, we ignore—they already exist.

    return SecurityGroupResult(group_id=group_id, name=group_name, created=created)


def ensure_key_pair(ec2_client, *, key_name: str, create_if_missing: bool, skip_check: bool, key_path: Optional[pathlib.Path]) -> None:
    """Ensure the key pair exists; optionally create and store locally."""

    if skip_check:
        print(f"Skipping AWS key pair validation - assuming '{key_name}' exists")
        return

    try:
        ec2_client.describe_key_pairs(KeyNames=[key_name])
        return
    except ClientError as exc:
        error_code = exc.response["Error"].get("Code")
        if error_code != "InvalidKeyPair.NotFound" or not create_if_missing:
            raise RuntimeError(
                f"Key pair '{key_name}' does not exist. Use --create-key to create it or --skip-key-check to bypass check."
            ) from exc

    response = ec2_client.create_key_pair(KeyName=key_name)
    material = response["KeyMaterial"]
    key_path = key_path or pathlib.Path(f"{key_name}.pem")
    key_path.write_text(material)
    key_path.chmod(0o600)
    print(f"Created key pair '{key_name}' and wrote private key to {key_path}.")


def fetch_latest_ami_id(ssm_client) -> str:
    parameter = ssm_client.get_parameter(Name=SSM_AMI_PARAMETER)
    return parameter["Parameter"]["Value"]


def launch_instance(ec2_resource, *, ami_id: str, key_name: str, security_group_id: str, public_ip: str):
    # Create user data with the actual public IP
    user_data = USER_DATA_TEMPLATE.replace("YOUR_INSTANCE_IP", public_ip)
    
    instances = ec2_resource.create_instances(
        ImageId=ami_id,
        InstanceType="t4g.micro",
        MinCount=1,
        MaxCount=1,
        KeyName=key_name,
        SecurityGroupIds=[security_group_id],
        UserData=user_data,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "FreeTier-Apache-5001"},
                    {"Key": "Purpose", "Value": "Apache demo"},
                ],
            }
        ],
    )
    return instances[0]


def wait_for_instance(instance):
    print("Waiting for instance to enter 'running' state...")
    instance.wait_until_running()
    # Wait for public IP to become available.
    instance.reload()
    while not instance.public_ip_address:
        time.sleep(5)
        instance.reload()
    return instance




if __name__ == "__main__":
    sys.exit(main())
