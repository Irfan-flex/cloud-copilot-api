# utils/aws_init.py
import boto3

_boto_clients = {}


def init_boto_clients():
    global _boto_clients
    services = ["ce", "ec2", "s3", "rds", "lambda",
                "ecr", "iam", "budgets", "cloudwatch", "compute-optimizer", "redshift", "elbv2"]
    for svc in services:
        _boto_clients[svc] = boto3.client(svc, region_name="us-east-1")


def get_boto_client(service):
    return _boto_clients.get(service)
