from flask import Blueprint, Flask, request, jsonify
from datetime import datetime, timedelta

from gevent import joinall, spawn
from services.recommend_service import (
    get_ec2_rightsizing_recommendations,
    get_ebs_rightsizing_recommendations,
    get_unattached_ebs_volumes,
    get_unassociated_elastic_ips,
    get_inactive_nat_gateways,
    get_ec2_instances_without_tags,
    get_reserved_instance_savings_opportunities,
    get_savings_plans_opportunities
)

recommend_blueprint = Blueprint('recommend', __name__)

# ----------------------------
# Rightsizing
# ----------------------------


@recommend_blueprint.route('/recommend/rightsizing-ec2', methods=['GET'])
def ec2_rightsizing():
    return jsonify(get_ec2_rightsizing_recommendations())


@recommend_blueprint.route('/recommend/rightsizing-ebs', methods=['GET'])
def ebs_rightsizing():
    return jsonify(get_ebs_rightsizing_recommendations())

# ----------------------------
# Cleanup
# ----------------------------


@recommend_blueprint.route('/recommend/unattached-ebs', methods=['GET'])
def unattached_ebs():
    region = request.args.get('region', 'us-east-1')
    return jsonify(get_unattached_ebs_volumes(region))


@recommend_blueprint.route('/recommend/cleanup/unassociated-eips', methods=['GET'])
def unassociated_eips():
    region = request.args.get('region', 'us-east-1')
    return jsonify(get_unassociated_elastic_ips(region))


@recommend_blueprint.route('/recommend/inactive-nats', methods=['GET'])
def inactive_nats():
    region = request.args.get('region', 'us-east-1')
    return jsonify(get_inactive_nat_gateways(region))

# ----------------------------
# Tagging Gaps
# ----------------------------


@recommend_blueprint.route('/recommend/untagged-ec2', methods=['GET'])
def untagged_ec2():
    region = request.args.get('region', 'us-east-1')
    return jsonify(get_ec2_instances_without_tags(region))

# ----------------------------
# Cost Explorer (RI & SP)
# ----------------------------


@recommend_blueprint.route('/recommend/savings-ri-opportunities', methods=['GET'])
def ri_opportunities():
    return jsonify(get_reserved_instance_savings_opportunities())


@recommend_blueprint.route('/recommend/savings-sp-opportunities', methods=['GET'])
def sp_opportunities():
    return jsonify(get_savings_plans_opportunities())

# ----------------------------
# Summary Route
# ----------------------------


@recommend_blueprint.route('/optimization/summary', methods=['GET'])
def optimization_summary():
    region = request.args.get('region', 'us-east-1')
    greenlets = [
        spawn(get_ec2_rightsizing_recommendations),
        spawn(get_ebs_rightsizing_recommendations),
        spawn(get_unattached_ebs_volumes, region),
        spawn(get_unassociated_elastic_ips, region),
        spawn(get_inactive_nat_gateways, region),
        spawn(get_ec2_instances_without_tags, region),
        spawn(get_reserved_instance_savings_opportunities),
        spawn(get_savings_plans_opportunities),
    ]
    joinall(greenlets)

    summary = {
        "rightsizing": {
            "ec2": greenlets[0].value,
            "ebs": greenlets[1].value
        },
        "cleanup": {
            "unattached_ebs": greenlets[2].value,
            "unassociated_eips": greenlets[3].value,
            "inactive_nats": greenlets[4].value
        },
        "tagging_gaps": {
            "ec2": greenlets[5].value
        },
        "savings": {
            "reserved_instance_opportunities": greenlets[6].value,
            "savings_plan_opportunities": greenlets[7].value
        }
    }
    return jsonify(summary)
