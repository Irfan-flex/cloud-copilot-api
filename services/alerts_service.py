from datetime import datetime, timedelta
import boto3
import logging

from services import cache_service

logger = logging.getLogger(__name__)
s3 = boto3.client("s3", region_name='us-east-1')
ecr = boto3.client("ecr", region_name='us-east-1')
ec2 = boto3.client("ec2", region_name='us-east-1')
budgets = boto3.client("budgets")
ce = boto3.client("ce", region_name='us-east-1')
cw = boto3.client("cloudwatch", region_name='us-east-1')
# ----------------------------
# 1. Resources without lifecycle policies
# ----------------------------


def get_s3_buckets_without_lifecycle():
    # Create a unique cache key based on input parameters
    cache_key = f"s3_buckets_without_lifecycle"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    """Return list of S3 buckets without lifecycle policy."""
    buckets = s3.list_buckets()["Buckets"]
    no_lifecycle = []
    for b in buckets:
        try:
            s3.get_bucket_lifecycle_configuration(Bucket=b["Name"])
        except s3.exceptions.NoSuchLifecycleConfiguration:
            no_lifecycle.append(b["Name"])

    # Store result in cache
    cache_service.set(cache_key, no_lifecycle)
    logger.info("Cached result for key: %s", cache_key)
    return no_lifecycle


def get_ecr_repos_without_lifecycle():
    # Create a unique cache key based on input parameters
    cache_key = f"ecr_repos_without_lifecycle"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result
    """Return list of ECR repos without lifecycle policy."""
    repos = ecr.describe_repositories()["repositories"]
    no_policy = []
    for r in repos:
        try:
            ecr.get_lifecycle_policy(repositoryName=r["repositoryName"])
        except ecr.exceptions.LifecyclePolicyNotFoundException:
            no_policy.append(r["repositoryName"])
    # Store result in cache
    cache_service.set(cache_key, no_policy)
    logger.info("Cached result for key: %s", cache_key)
    return no_policy


# ----------------------------
# 2. Security / compliance overlap
# ----------------------------

def get_unrestricted_security_groups():
    # Create a unique cache key based on input parameters
    cache_key = f"unrestricted_security_groups"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return list(set(cached_result))
    """Return security groups with wide-open inbound rules (0.0.0.0/0 or ::/0)."""
    sgs = ec2.describe_security_groups()["SecurityGroups"]
    open_sgs = []
    for sg in sgs:
        for perm in sg.get("IpPermissions", []):
            for ip_range in perm.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    open_sgs.append(sg["GroupId"])
            for ipv6_range in perm.get("Ipv6Ranges", []):
                if ipv6_range.get("CidrIpv6") == "::/0":
                    open_sgs.append(sg["GroupId"])
    # Store result in cache
    cache_service.set(cache_key, open_sgs)
    logger.info("Cached result for key: %s", cache_key)
    return list(set(open_sgs))


def get_unencrypted_s3_buckets():
    # Create a unique cache key based on input parameters
    cache_key = f"unencrypted_s3_buckets"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result
    """Return list of S3 buckets without encryption enabled."""
    buckets = s3.list_buckets()["Buckets"]
    unencrypted = []
    for b in buckets:
        try:
            s3.get_bucket_encryption(Bucket=b["Name"])
        except s3.exceptions.ClientError:
            unencrypted.append(b["Name"])
    # Store result in cache
    cache_service.set(cache_key, unencrypted)
    logger.info("Cached result for key: %s", cache_key)
    return unencrypted


# ----------------------------
# 3. Budget vs Actual
# ----------------------------

def get_budget_vs_actual():
    # Create a unique cache key based on input parameters
    cache_key = f"budget_vs_actual"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    """Return AWS Budgets (if set) with actual spend vs budgeted amount."""
    results = []
    response = budgets.describe_budgets(
        AccountId=boto3.client("sts", region_name='us-east-1').get_caller_identity()["Account"])
    for budget in response.get("Budgets", []):
        budget_name = budget["BudgetName"]
        actual = budgets.describe_budget_performance_history(
            AccountId=boto3.client(
                "sts", region_name='us-east-1').get_caller_identity()["Account"],
            BudgetName=budget_name
        )
        results.append({
            "BudgetName": budget_name,
            "Limit": budget["BudgetLimit"]["Amount"] + " " + budget["BudgetLimit"]["Unit"],
            "ActualSpend": budget["CalculatedSpend"]["ActualSpend"]["Amount"] + " " + budget["CalculatedSpend"]["ActualSpend"]["Unit"],
        })
    # Store result in cache
    cache_service.set(cache_key, results)
    logger.info("Cached result for key: %s", cache_key)
    return results


# ----------------------------
# 4. Custom alerts (spend threshold, idle detection)
# ----------------------------

def check_spend_threshold(threshold_usd, start_date=None, end_date=None):
    """Check if spend exceeds threshold for given period."""

    if not start_date or not end_date:
        # default: current month
        today = datetime.utcnow()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )

    amount = float(response["ResultsByTime"][0]
                   ["Total"]["UnblendedCost"]["Amount"])
    return amount > threshold_usd, amount


def get_idle_ec2_instances(idle_cpu_threshold=5, days=7):
    # Create a unique cache key based on input parameters
    cache_key = f"idle_ec2_instances"

    # Try to get cached result
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        logger.info("Returning cached result for key: %s", cache_key)
        return cached_result

    """Return EC2 instances with very low CPU utilization (CloudWatch check)."""

    instances = ec2.describe_instances()
    idle_instances = []
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            metrics = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=datetime.utcnow() - timedelta(days=days),
                EndTime=datetime.utcnow(),
                Period=3600,
                Statistics=["Average"]
            )
            if metrics["Datapoints"]:
                avg_cpu = sum(
                    d["Average"] for d in metrics["Datapoints"]) / len(metrics["Datapoints"])
                if avg_cpu < idle_cpu_threshold:
                    idle_instances.append({
                        "instance_id": instance_id,
                        "avg_cpu": avg_cpu
                    })
    # Store result in cache
    cache_service.set(cache_key, idle_instances)
    logger.info("Cached result for key: %s", cache_key)
    return idle_instances
