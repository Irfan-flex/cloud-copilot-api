# # Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# # Unauthorized copying of this file, via any medium is strictly prohibited
# # Proprietary and confidential
# # See file LICENSE.txt for full license details.
# from decimal import Decimal
# import json
# import boto3
# from flask import Blueprint, request, Response
# from botocore.exceptions import ClientError
# from services.cost_service import get_cost_data


# health_blueprint = Blueprint('health', __name__)


# class DecimalEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Decimal):
#             return float(obj)
#         return super(DecimalEncoder, self).default(obj)


# @health_blueprint.route("/health", methods=["GET"])
# def health():
#     """
#     returns the string "OK" to check if the server is running.
#     """
#     return "OK"


# @health_blueprint.route("/recommend", methods=["GET"])
# def recommend():
#     """
#     returns the string "OK" to check if the server is running.
#     """
#     results = []
#     co = boto3.client("compute-optimizer")
#     response = co.get_ec2_instance_recommendations()
#     results = []
#     for rec in response.get("instanceRecommendations", []):
#         results.append({
#             "instanceArn": rec["instanceArn"],
#             "recommendations": rec["recommendationOptions"]
#         })
#     return Response(json.dumps(results, cls=DecimalEncoder), mimetype="application/json")


# @health_blueprint.route("/idle", methods=["GET"])
# def idle():
#     """
#     returns the string "OK" to check if the server is running.
#     """
#     support = boto3.client("support", region_name="us-east-1")

#     checks = support.describe_trusted_advisor_checks(language="en")

#     results = []
#     for check in checks.get("checks", []):
#         if check["category"] == "cost_optimizing":
#             results.append({
#                 "id": check["id"],
#                 "name": check["name"]
#             })
#     return Response(json.dumps(results, cls=DecimalEncoder), mimetype="application/json")


# @health_blueprint.route("/cost", methods=["GET"])
# def cost():
#     """
#     returns the string "OK" to check if the server is running.
#     """
#     ce = boto3.client("ce")
#     response = ce.get_cost_and_usage(
#         TimePeriod={
#             "Start": "2025-08-01",
#             "End": "2025-08-31"
#         },
#         Granularity="MONTHLY",
#         Metrics=["UnblendedCost"],
#         GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
#     )
#     return Response(json.dumps(response, cls=DecimalEncoder), mimetype="application/json")


# ec2 = boto3.client("ec2")


# @health_blueprint.route("/instances", methods=["GET"])
# def list_instances():
#     """
#     Returns EC2 instance details: ID, state, tags, and attached volumes
#     """
#     try:
#         response = ec2.describe_instances()
#         results = []

#         for reservation in response.get("Reservations", []):
#             for instance in reservation.get("Instances", []):
#                 instance_data = {
#                     "InstanceId": instance.get("InstanceId"),
#                     "State": instance.get("State", {}).get("Name"),
#                     "InstanceType": instance.get("InstanceType"),
#                     "AvailabilityZone": instance.get("Placement", {}).get("AvailabilityZone"),
#                     "Tags": [
#                         {"Key": tag["Key"], "Value": tag["Value"]}
#                         for tag in instance.get("Tags", [])
#                     ],
#                     "Volumes": []
#                 }

#                 # Flatten volumes
#                 for mapping in instance.get("BlockDeviceMappings", []):
#                     ebs = mapping.get("Ebs")
#                     if ebs:
#                         instance_data["Volumes"].append({
#                             "VolumeId": ebs.get("VolumeId"),
#                             "Status": ebs.get("Status")
#                         })

#                 results.append(instance_data)

#         return Response(json.dumps(results, indent=2), mimetype="application/json")

#     except Exception as e:
#         return Response(
#             json.dumps({"error": str(e)}),
#             status=500,
#             mimetype="application/json"
#         )


# @health_blueprint.route("/idle-resources", methods=["GET"])
# def list_idle_resources():
#     results = []

#     try:
#         ec2 = boto3.client("ec2")

#         # 1. Stopped EC2 instances
#         instances = ec2.describe_instances(
#             Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
#         )
#         stopped = []
#         for reservation in instances["Reservations"]:
#             for instance in reservation["Instances"]:
#                 stopped.append({
#                     "id": instance["InstanceId"],
#                     "type": "EC2 Instance",
#                     "state": "stopped",
#                     "tags": instance.get("Tags", [])
#                 })
#         if stopped:
#             results.append(
#                 {"check": "Stopped EC2 Instances", "resources": stopped})

#         # 2. Unattached EBS volumes
#         volumes = ec2.describe_volumes(
#             Filters=[{"Name": "status", "Values": ["available"]}]
#         )
#         unattached = [
#             {"id": v["VolumeId"], "size": v["Size"], "tags": v.get("Tags", [])}
#             for v in volumes["Volumes"]
#         ]
#         if unattached:
#             results.append(
#                 {"check": "Unattached EBS Volumes", "resources": unattached})

#         # 3. Idle Load Balancers (no targets registered)
#         elb = boto3.client("elbv2")
#         lbs = elb.describe_load_balancers()
#         idle_lbs = []
#         for lb in lbs["LoadBalancers"]:
#             target_groups = elb.describe_target_groups(
#                 LoadBalancerArn=lb["LoadBalancerArn"])
#             has_targets = False
#             for tg in target_groups.get("TargetGroups", []):
#                 targets = elb.describe_target_health(
#                     TargetGroupArn=tg["TargetGroupArn"])
#                 if targets.get("TargetHealthDescriptions"):
#                     has_targets = True
#             if not has_targets:
#                 idle_lbs.append(
#                     {"id": lb["LoadBalancerArn"], "name": lb["LoadBalancerName"]})
#         if idle_lbs:
#             results.append(
#                 {"check": "Idle Load Balancers", "resources": idle_lbs})

#     except ClientError as e:
#         print(f"Error: {e}")

#     return results
