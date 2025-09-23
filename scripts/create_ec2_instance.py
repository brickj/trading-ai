"""Utilities for provisioning a high-performance EC2 instance for the trading AI project."""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError


# Replace this with the absolute path to the PEM key that should be created/used.
PEM_KEY_PATH = "/path/to/your-key.pem"


@dataclass
class EC2Config:
    """Configuration values for the EC2 instance launch."""

    region_name: str = "us-east-1"
    key_pair_name: str = "trading-ai-key"
    vpc_id: str | None = None  # If None, the default VPC is used.
    subnet_id: str | None = None  # Optional specific subnet.
    security_group_name: str = "trading-ai-sg"
    instance_type: str = "p4d.24xlarge"  # Extremely powerful GPU instance.
    volume_size_gb: int = 200
    iam_instance_profile: str | None = None


class EC2Provisioner:
    """Provisioner that encapsulates EC2 instance creation steps."""

    def __init__(self, config: EC2Config) -> None:
        self.config = config
        self.ec2 = boto3.client("ec2", region_name=config.region_name)

    def ensure_key_pair(self) -> str:
        """Ensure that a key pair exists and is saved to the PEM path."""

        if os.path.exists(PEM_KEY_PATH):
            return self.config.key_pair_name

        try:
            key_pair = self.ec2.create_key_pair(KeyName=self.config.key_pair_name)
        except ClientError as exc:
            raise RuntimeError(f"Unable to create key pair: {exc}") from exc

        private_key_material = key_pair["KeyMaterial"]
        os.makedirs(os.path.dirname(PEM_KEY_PATH) or ".", exist_ok=True)
        with open(PEM_KEY_PATH, "w", encoding="utf-8") as pem_file:
            pem_file.write(private_key_material)

        os.chmod(PEM_KEY_PATH, stat.S_IRUSR | stat.S_IWUSR)
        print(f"Created key pair '{self.config.key_pair_name}' at {PEM_KEY_PATH}")
        return self.config.key_pair_name

    def ensure_security_group(self) -> str:
        """Create or retrieve the security group that allows SSH/HTTP access."""

        try:
            response = self.ec2.describe_security_groups(GroupNames=[self.config.security_group_name])
            group_id = response["SecurityGroups"][0]["GroupId"]
            return group_id
        except ClientError as exc:
            if exc.response["Error"].get("Code") != "InvalidGroup.NotFound":
                raise

        vpc_id = self.config.vpc_id
        if not vpc_id:
            vpcs = self.ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
            if not vpcs:
                raise RuntimeError("No default VPC found; please specify vpc_id in EC2Config.")
            vpc_id = vpcs[0]["VpcId"]

        sg = self.ec2.create_security_group(
            GroupName=self.config.security_group_name,
            Description="Security group for trading AI deployment",
            VpcId=vpc_id,
        )
        group_id = sg["GroupId"]
        self.ec2.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH access"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTP access"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 443,
                    "ToPort": 443,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTPS access"}],
                },
            ],
        )
        print(f"Created security group '{self.config.security_group_name}' with id {group_id}")
        return group_id

    def resolve_latest_ami(self) -> str:
        """Retrieve the latest Amazon Linux 2023 AMI via SSM."""

        ssm = boto3.client("ssm", region_name=self.config.region_name)
        parameter = ssm.get_parameter(Name="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64")
        return parameter["Parameter"]["Value"]

    def create_instance(self) -> None:
        """Create and tag the high-performance EC2 instance."""

        key_pair_name = self.ensure_key_pair()
        security_group_id = self.ensure_security_group()
        ami_id = self.resolve_latest_ami()

        launch_params = {
            "ImageId": ami_id,
            "InstanceType": self.config.instance_type,
            "KeyName": key_pair_name,
            "SecurityGroupIds": [security_group_id],
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "VolumeSize": self.config.volume_size_gb,
                        "VolumeType": "gp3",
                        "DeleteOnTermination": True,
                        "Encrypted": True,
                    },
                }
            ],
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": "trading-ai-prod"},
                        {"Key": "Project", "Value": "trading-ai"},
                    ],
                }
            ],
            "MinCount": 1,
            "MaxCount": 1,
        }

        if self.config.subnet_id:
            launch_params["SubnetId"] = self.config.subnet_id
        if self.config.iam_instance_profile:
            launch_params["IamInstanceProfile"] = {"Name": self.config.iam_instance_profile}

        try:
            response = self.ec2.run_instances(**launch_params)
        except ClientError as exc:
            raise RuntimeError(f"Failed to launch instance: {exc}") from exc

        instance = response["Instances"][0]
        instance_id = instance["InstanceId"]
        print(f"Launched instance {instance_id} with type {self.config.instance_type}")

        waiter = self.ec2.get_waiter("instance_status_ok")
        print("Waiting for instance to reach 'running' and status checks to pass...")
        waiter.wait(InstanceIds=[instance_id])

        describe = self.ec2.describe_instances(InstanceIds=[instance_id])
        public_dns = describe["Reservations"][0]["Instances"][0].get("PublicDnsName", "")
        public_ip = describe["Reservations"][0]["Instances"][0].get("PublicIpAddress", "")
        print(f"Instance ready. Public DNS: {public_dns} | Public IP: {public_ip}")


def main() -> None:
    try:
        provisioner = EC2Provisioner(EC2Config())
        provisioner.create_instance()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error during provisioning: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
