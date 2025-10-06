from flask import Blueprint, Flask, request, jsonify
from datetime import datetime, timedelta

from gevent import joinall, spawn
from services.utilisation_service import (
    get_stopped_ec2_instances,
    get_unattached_ebs_volumes,
    get_idle_rds_instances,
    get_underutilized_redshift,
    get_idle_load_balancers,
    get_overprovisioned_ec2,
    get_overprovisioned_lambdas,
    get_overprovisioned_ebs
)

utilisation_blueprint = Blueprint('utilisation', __name__)


def parse_dates():
    """Parse start and end date from query params, return UTC datetime objects"""
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        start_dt = datetime.strptime(
            start, "%Y-%m-%d") if start else datetime.utcnow() - timedelta(days=7)
        end_dt = datetime.strptime(
            end, "%Y-%m-%d") if end else datetime.utcnow()
    except ValueError:
        return None, None, "Invalid date format. Use YYYY-MM-DD."
    return start_dt, end_dt, None


@utilisation_blueprint.route("/idle/ec2", methods=["GET"])
def idle_ec2():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    instances = get_stopped_ec2_instances()
    return jsonify({"stopped_ec2_instances": instances})


@utilisation_blueprint.route("/idle/ebs", methods=["GET"])
def idle_ebs():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    volumes = get_unattached_ebs_volumes()
    return jsonify({"unattached_ebs_volumes": volumes})


@utilisation_blueprint.route("/idle/rds", methods=["GET"])
def idle_rds():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    idle = get_idle_rds_instances()
    return jsonify({"idle_rds_instances": idle})


@utilisation_blueprint.route("/idle/redshift", methods=["GET"])
def idle_redshift():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    underutilized = get_underutilized_redshift()
    return jsonify({"underutilized_redshift_clusters": underutilized})


@utilisation_blueprint.route("/idle/loadbalancers", methods=["GET"])
def idle_lbs():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    idle = get_idle_load_balancers()
    return jsonify({"idle_load_balancers": idle})


@utilisation_blueprint.route("/overprovisioned/ec2", methods=["GET"])
def overprovisioned_ec2():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    over = get_overprovisioned_ec2()
    return jsonify({"overprovisioned_ec2": over})


@utilisation_blueprint.route("/overprovisioned/lambda", methods=["GET"])
def overprovisioned_lambda():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    over = get_overprovisioned_lambdas()
    return jsonify({"overprovisioned_lambda": over})


@utilisation_blueprint.route("/overprovisioned/ebs", methods=["GET"])
def overprovisioned_ebs():
    start_dt, end_dt, err = parse_dates()
    if err:
        return jsonify({"error": err}), 400
    over = get_overprovisioned_ebs()
    return jsonify({"overprovisioned_ebs": over})


@utilisation_blueprint.route('/utilisation/summary', methods=['GET'])
def optimization_summary():
    start_dt, end_dt, err = parse_dates()

    region = request.args.get('region', 'us-east-1')
    greenlets = [
        spawn(get_stopped_ec2_instances),
        spawn(get_unattached_ebs_volumes),
        spawn(get_idle_rds_instances),
        spawn(get_underutilized_redshift),
        spawn(get_idle_load_balancers),
        spawn(get_overprovisioned_ec2),
        spawn(get_overprovisioned_lambdas),
        spawn(get_overprovisioned_ebs),

    ]
    joinall(greenlets)

    summary = {
        "stopped_ec2_instances": greenlets[0].value,
        "unattached_ebs_volumes": greenlets[1].value,
        "idle_rds_instances": greenlets[2].value,
        "underutilized_redshift_clusters": greenlets[3].value,
        "idle_load_balancers": greenlets[4].value,
        "overprovisioned_ec2": greenlets[5].value,
        "overprovisioned_lambda": greenlets[6].value,
        "overprovisioned_ebs": greenlets[7].value,
    }
    return jsonify(summary)
