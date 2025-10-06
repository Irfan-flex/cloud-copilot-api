from datetime import datetime, timedelta
import boto3

from services import cache_service
import logging

logger = logging.getLogger(__name__)

# ec2 = boto3.client("ec2")
ec2 = boto3.client("ec2", region_name="us-east-1")
cw = boto3.client("cloudwatch", region_name="us-east-1")
s3 = boto3.client("s3", region_name="us-east-1")
rds = boto3.client("rds", region_name="us-east-1")
lam = boto3.client("lambda", region_name="us-east-1")
cw = boto3.client("cloudwatch", region_name="us-east-1")

# ---------- EC2 ----------


def list_ec2_instances():
    # Create a unique cache key based on input parameters
    cache_key = f"list_ec2_instances"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    instances = []
    reservations = ec2.describe_instances()["Reservations"]

    for res in reservations:
        for inst in res["Instances"]:
            tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
            instances.append({
                "id": inst["InstanceId"],
                "type": inst["InstanceType"],
                "state": inst["State"]["Name"],
                "region": ec2.meta.region_name,
                "tags": tags
            })
    # Store result in cache
    cache_service.set(cache_key, instances)
    logger.info("Cached result for key: %s", cache_key)
    return instances


# ---------- EBS ----------
def list_ebs_volumes():
    # Create a unique cache key based on input parameters
    cache_key = f"list_ebs_volumes"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result
    volumes = []
    for v in ec2.describe_volumes()["Volumes"]:
        tags = {t["Key"]: t["Value"] for t in v.get("Tags", [])}
        volumes.append({
            "id": v["VolumeId"],
            "size": v["Size"],
            "iops": v.get("Iops"),
            "state": v["State"],
            "attached": bool(v["Attachments"]),
            "last_attached": v["Attachments"][0]["AttachTime"].isoformat() if v["Attachments"] else None,
            "Name": tags
        })
    # Store result in cache
    cache_service.set(cache_key, volumes)
    logger.info("Cached result for key: %s", cache_key)
    return volumes


# ---------- S3 ----------
def list_s3_buckets():
    # Create a unique cache key based on input parameters
    cache_key = f"list_s3_buckets"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result
    buckets = []
    for b in s3.list_buckets()["Buckets"]:
        bucket_name = b["Name"]

        # Get encryption
        try:
            enc = s3.get_bucket_encryption(Bucket=bucket_name)
            encryption = enc["ServerSideEncryptionConfiguration"]
        except:
            encryption = "None"

        # Get versioning
        ver = s3.get_bucket_versioning(
            Bucket=bucket_name).get("Status", "Disabled")

        # Get lifecycle
        try:
            lifecycle = s3.get_bucket_lifecycle_configuration(
                Bucket=bucket_name)
        except:
            lifecycle = "None"

        buckets.append({
            "name": bucket_name,
            "versioning": ver,
            "encryption": encryption,
            "lifecycle": lifecycle
        })
    # Store result in cache
    cache_service.set(cache_key, buckets)
    logger.info("Cached result for key: %s", cache_key)
    return buckets


# ---------- RDS ----------
def list_rds_instances():
    # Create a unique cache key based on input parameters
    cache_key = f"list_rds_instances"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result
    dbs = []
    for db in rds.describe_db_instances()["DBInstances"]:
        arn = db["DBInstanceArn"]
        tags = {t["Key"]: t["Value"]
                for t in rds.list_tags_for_resource(ResourceName=arn)["TagList"]}
        dbs.append({
            "id": db["DBInstanceIdentifier"],
            "type": db["DBInstanceClass"],
            "status": db["DBInstanceStatus"],
            "storage": db["AllocatedStorage"],
            "tags": tags
        })
    # Store result in cache
    cache_service.set(cache_key, dbs)
    logger.info("Cached result for key: %s", cache_key)
    return dbs


# ---------- Lambda ----------
def list_lambda_functions():
    # Create a unique cache key based on input parameters
    cache_key = f"list_lambda_functions"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    functions = []
    for f in lam.list_functions()["Functions"]:
        name = f["FunctionName"]
        mem = f["MemorySize"]
        timeout = f["Timeout"]

        # Example: Get invocation count vs errors (last 1 hour)
        inv = cw.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Invocations",
            Dimensions=[{"Name": "FunctionName", "Value": name}],
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=["Sum"]
        )
        err = cw.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Errors",
            Dimensions=[{"Name": "FunctionName", "Value": name}],
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=["Sum"]
        )
        invocations = inv["Datapoints"][0]["Sum"] if inv["Datapoints"] else 0
        errors = err["Datapoints"][0]["Sum"] if err["Datapoints"] else 0

        functions.append({
            "name": name,
            "memory": mem,
            "timeout": timeout,
            "invocations": invocations,
            "errors": errors
        })
     # Store result in cache
    cache_service.set(cache_key, functions)
    logger.info("Cached result for key: %s", cache_key)
    return functions
