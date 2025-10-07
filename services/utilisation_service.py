from datetime import datetime, timedelta
import boto3
import logging

from services import cache_service

logger = logging.getLogger(__name__)

# 1. Stopped / unused EC2

ec2 = boto3.client("ec2", region_name="us-east-1")
rds = boto3.client("rds", region_name="us-east-1")
cw = boto3.client("cloudwatch", region_name="us-east-1")
redshift = boto3.client("redshift", region_name="us-east-1")
elbv2 = boto3.client("elbv2", region_name="us-east-1")
lambda_client = boto3.client("lambda", region_name="us-east-1")


def get_stopped_ec2_instances():
    # Create a unique cache key based on input parameters
    cache_key = f"get_stopped_ec2_instances"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}])
    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append(instance["InstanceId"])
    cache_service.set(cache_key, instances)
    logger.info("Cached result for key: %s", cache_key)
    return instances


# 2. Unattached EBS volumes
def get_unattached_ebs_volumes():
    # Create a unique cache key based on input parameters
    cache_key = f"get_unattached_ebs_volumes"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    response = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}])
    result = [vol["VolumeId"] for vol in response["Volumes"]]
    cache_service.set(cache_key, result)
    logger.info("Cached result for key: %s", cache_key)
    return result


# 3. Idle RDS (no connections, low CPU)
def get_idle_rds_instances(cloudwatch_period=3600):
    # Create a unique cache key based on input parameters
    cache_key = f"get_idle_rds_instances"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    instances = rds.describe_db_instances()["DBInstances"]
    idle = []
    for db in instances:
        metrics = cw.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "DBInstanceIdentifier",
                         "Value": db["DBInstanceIdentifier"]}],
            StartTime=datetime.utcnow() - timedelta(seconds=cloudwatch_period * 24),
            EndTime=datetime.utcnow(),
            Period=cloudwatch_period,
            Statistics=["Average"]
        )
        if not metrics["Datapoints"] or metrics["Datapoints"][0]["Average"] < 5:  # <5% CPU avg
            idle.append(db["DBInstanceIdentifier"])
    cache_service.set(cache_key, idle)
    logger.info("Cached result for key: %s", cache_key)
    return idle


# 4. Underutilized Redshift clusters
def get_underutilized_redshift(cloudwatch_period=3600):
    # Create a unique cache key based on input parameters
    cache_key = f"get_underutilized_redshift"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result
    clusters = redshift.describe_clusters()["Clusters"]

    underutilized = []
    for cluster in clusters:
        metrics = cw.get_metric_statistics(
            Namespace="AWS/Redshift",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "ClusterIdentifier",
                         "Value": cluster["ClusterIdentifier"]}],
            StartTime=datetime.utcnow() - timedelta(seconds=cloudwatch_period * 24),
            EndTime=datetime.utcnow(),
            Period=cloudwatch_period,
            Statistics=["Average"]
        )
        if not metrics["Datapoints"] or metrics["Datapoints"][0]["Average"] < 10:  # <10% avg CPU
            underutilized.append(cluster["ClusterIdentifier"])
    cache_service.set(cache_key, underutilized)
    logger.info("Cached result for key: %s", cache_key)
    return underutilized


# 5. Idle / unused Load Balancers (very low request count)
def get_idle_load_balancers(cloudwatch_period=3600):
    # Create a unique cache key based on input parameters
    cache_key = f"get_idle_load_balancers"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    lbs = elbv2.describe_load_balancers()["LoadBalancers"]

    idle = []
    for lb in lbs:
        metrics = cw.get_metric_statistics(
            Namespace="AWS/ApplicationELB",
            MetricName="RequestCount",
            Dimensions=[{"Name": "LoadBalancer", "Value": lb["LoadBalancerArn"].split(
                ":loadbalancer/")[1]}],
            # StartTime=datetime.utcnow() - timedelta(seconds=cloudwatch_period * 24),
            StartTime=datetime.utcnow() - timedelta(days=30),  # 30 days back
            EndTime=datetime.utcnow(),
            Period=cloudwatch_period,
            Statistics=["Sum"]
        )
        if not metrics["Datapoints"] or metrics["Datapoints"][0]["Sum"] == 0:
            idle.append(lb["LoadBalancerName"])
    cache_service.set(cache_key, idle)
    logger.info("Cached result for key: %s", cache_key)
    return idle

# 6. EC2 with very low CPU utilization vs size


def get_overprovisioned_ec2(cloudwatch_period=3600):
    # Create a unique cache key based on input parameters
    cache_key = f"get_overprovisioned_ec2"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    reservations = ec2.describe_instances()["Reservations"]

    overprovisioned = []
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]

            metrics = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=datetime.utcnow() - timedelta(seconds=cloudwatch_period * 24),
                EndTime=datetime.utcnow(),
                Period=cloudwatch_period,
                Statistics=["Average"]
            )
            if metrics["Datapoints"] and metrics["Datapoints"][0]["Average"] < 5:  # <5% avg
                overprovisioned.append(
                    {"InstanceId": instance_id, "Type": instance_type})
    cache_service.set(cache_key, overprovisioned)
    logger.info("Cached result for key: %s", cache_key)
    return overprovisioned


# 7. Lambda with high memory but low usage
def get_overprovisioned_lambdas():
    # Create a unique cache key based on input parameters
    cache_key = f"get_overprovisioned_lambdas"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    functions = lambda_client.list_functions()["Functions"]
    overprovisioned = []

    for fn in functions:
        fn_name = fn["FunctionName"]
        mem = fn["MemorySize"]

        metrics = cw.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Invocations",
            Dimensions=[{"Name": "FunctionName", "Value": fn_name}],
            StartTime=datetime.utcnow() - timedelta(days=7),
            EndTime=datetime.utcnow(),
            Period=3600,
            Statistics=["Sum"]
        )
        invocations = sum(
            dp["Sum"] for dp in metrics["Datapoints"]) if metrics["Datapoints"] else 0

        if mem > 512 and invocations < 10:  # heuristic
            overprovisioned.append(
                {"FunctionName": fn_name, "Memory": mem, "Invocations": invocations})
    cache_service.set(cache_key, overprovisioned)
    logger.info("Cached result for key: %s", cache_key)
    return overprovisioned


# 8. EBS volumes much larger than needed (low IOPS)
def get_overprovisioned_ebs(cloudwatch_period=3600):
    # Create a unique cache key based on input parameters
    cache_key = f"get_overprovisioned_ebs"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    volumes = ec2.describe_volumes()["Volumes"]
    overprovisioned = []

    for vol in volumes:
        metrics = cw.get_metric_statistics(
            Namespace="AWS/EBS",
            MetricName="VolumeReadOps",
            Dimensions=[{"Name": "VolumeId", "Value": vol["VolumeId"]}],
            StartTime=datetime.utcnow() - timedelta(seconds=cloudwatch_period * 24),
            EndTime=datetime.utcnow(),
            Period=cloudwatch_period,
            Statistics=["Sum"]
        )
        total_ops = sum(dp["Sum"] for dp in metrics["Datapoints"]
                        ) if metrics["Datapoints"] else 0
        if vol["Size"] > 100 and total_ops < 50:  # >100GB but hardly used
            overprovisioned.append(vol["VolumeId"])
    cache_service.set(cache_key, overprovisioned)
    logger.info("Cached result for key: %s", cache_key)
    return overprovisioned
