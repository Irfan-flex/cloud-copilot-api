from decimal import Decimal
import json
import boto3
from flask import Blueprint, request, Response, jsonify
from botocore.exceptions import ClientError
from gevent import joinall, spawn
from datetime import datetime

from services.alerts_service import check_spend_threshold, get_idle_ec2_instances, get_s3_buckets_without_lifecycle, get_ecr_repos_without_lifecycle, get_budget_vs_actual, get_unencrypted_s3_buckets, get_unrestricted_security_groups


alerts_blueprint = Blueprint('alerts', __name__)


# ----------------------------
# Governance
# ----------------------------

# @alerts_blueprint.route("/alerts/s3/no-lifecycle", methods=["GET"])
# def s3_no_lifecycle():
#     result = get_s3_buckets_without_lifecycle()
#     return {"buckets_without_lifecycle": result}


@alerts_blueprint.route("/alerts/ecr/no-lifecycle", methods=["GET"])
def ecr_no_lifecycle():
    result = get_ecr_repos_without_lifecycle()
    return {"repos_without_lifecycle": result}


# ----------------------------
# Security / Compliance
# ----------------------------

@alerts_blueprint.route("/alerts/security/unrestricted-sgs", methods=["GET"])
def unrestricted_sgs():
    result = get_unrestricted_security_groups()
    return {"unrestricted_security_groups": result}


@alerts_blueprint.route("/alerts/security/unencrypted-buckets", methods=["GET"])
def unencrypted_buckets():
    result = get_unencrypted_s3_buckets()
    return {"unencrypted_buckets": result}


# ----------------------------
# Budgets
# ----------------------------

@alerts_blueprint.route("/alerts/budgets", methods=["GET"])
def budget_vs_actual():
    result = get_budget_vs_actual()
    return {"budgets": result}


# ----------------------------
# Custom Alerts
# ----------------------------

@alerts_blueprint.route("/alerts/spend-threshold", methods=["GET"])
def spend_threshold():
    """
    Params: 
      threshold (float, required)
      start_date (YYYY-MM-DD, optional)
      end_date (YYYY-MM-DD, optional)
    """
    threshold = float(request.args.get("threshold", 100.0))
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    result = check_spend_threshold(
        threshold_usd=threshold,
        start_date=start_date,
        end_date=end_date
    )
    return {
        "threshold": threshold,
        "exceeded": result[0],
        "actual_spend": result[1]
    }


@alerts_blueprint.route("/alerts/idle-ec2", methods=["GET"])
def idle_ec2():
    """
    Params:
      threshold (float, optional, default=5)
      days (int, optional, default=7)
    """
    threshold = float(request.args.get("threshold", 5))
    days = int(request.args.get("days", 7))

    result = get_idle_ec2_instances(
        idle_cpu_threshold=threshold,
        days=days
    )
    return {"idle_instances": result}

@alerts_blueprint.route('/alerts/summary', methods=['GET'])
def inventory_summary():
    threshold = float(request.args.get("threshold", 100.0))
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if start_date and end_date:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end_date_dt - start_date_dt).days
    else:
        days = 7  # default value

    greenlets = [
        spawn(get_idle_ec2_instances, idle_cpu_threshold=threshold, days=days),
        spawn(get_ecr_repos_without_lifecycle),
        spawn(get_unrestricted_security_groups),
        spawn(get_unencrypted_s3_buckets),
        spawn(get_budget_vs_actual),
        spawn(check_spend_threshold, threshold_usd=threshold, start_date=start_date, end_date=end_date),
    ]
    joinall(greenlets)

    summary = {
        "idle_ec2_instances": greenlets[0].value,
        "ecr_repos_without_lifecycle": greenlets[1].value,
        "unrestricted_security_groups": greenlets[2].value,
        "unencrypted_s3_buckets": greenlets[3].value,
        "budget_vs_actual": greenlets[4].value,
        "spend_threshold": greenlets[5].value,
    }
    return jsonify(summary)