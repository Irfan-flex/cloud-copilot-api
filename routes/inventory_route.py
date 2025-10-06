from decimal import Decimal
import json
import boto3
from flask import Blueprint, request, Response, jsonify
from botocore.exceptions import ClientError
from services.inventory_service import list_ec2_instances, list_ebs_volumes, list_lambda_functions, list_rds_instances, list_s3_buckets
from gevent import joinall, spawn


inventory_blueprint = Blueprint('inventory', __name__)


@inventory_blueprint.route("/ec2", methods=["GET"])
def list_ec2():
    return list_ec2_instances()


@inventory_blueprint.route("/ebs", methods=["GET"])
def list_ebs():
    return list_ebs_volumes()


# @inventory_blueprint.route("/s3", methods=["GET"])
# def list_s3():
#     return list_s3_buckets()


@inventory_blueprint.route("/lambda", methods=["GET"])
def list_lambda():
    return list_lambda_functions()


@inventory_blueprint.route("/rds", methods=["GET"])
def list_rds():
    return list_rds_instances()


@inventory_blueprint.route('/inventory/summary', methods=['GET'])
def inventory_summary():
    # start_dt, end_dt, err = parse_dates()

    region = request.args.get('region', 'us-east-1')
    greenlets = [
        spawn(list_ec2_instances),
        spawn(list_ebs_volumes),
        spawn(list_lambda_functions),
        spawn(list_rds_instances),
    ]
    joinall(greenlets)

    summary = {
        "ec2_instances": greenlets[0].value,
        "ebs_volumes": greenlets[1].value,
        "lambda_functions": greenlets[2].value,
        "rds_instances": greenlets[3].value,
    }
    return jsonify(summary)
