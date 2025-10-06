from decimal import Decimal
import json
import boto3
from flask import Blueprint, jsonify, request, Response
from botocore.exceptions import ClientError
from services.cost_service import cost_by_service, cost_by_tag, forecasted_spend, get_cost_anomalies, get_cost_data, get_daily_cost_trend, iso_date, total_cost_trend
from datetime import date, datetime, timedelta

cost_blueprint = Blueprint('cost', __name__, url_prefix='/cost')


def parse_dates():
    """Parse ?start=YYYY-MM-DD&end=YYYY-MM-DD, default = last 30 days."""
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if start_str and end_str:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
    else:
        end = date.today()
        start = end - timedelta(days=30)
    return start, end


# @cost_blueprint.route("/total-cost", methods=["GET"])
# def total_cost():
#     return get_cost_data()


@cost_blueprint.route("/total-cost", methods=["GET"])  # ✅
def api_total_spend():
    """Total spend between start and end (compares previous period of same length)."""
    start, end = parse_dates()
    period_days = (end - start).days

    # Current period
    this_period = total_cost_trend(
        iso_date(start), iso_date(end), granularity='MONTHLY')
    # Previous period of same length
    prev_end = start
    prev_start = prev_end - timedelta(days=period_days)
    last_period = total_cost_trend(
        iso_date(prev_start), iso_date(prev_end), granularity='MONTHLY')

    return {"this_month": this_period, "last_month": last_period}


@cost_blueprint.route("/cost_breakdown", methods=["GET"])  # ✅
def api_cost_breakdown():
    """Cost breakdown by AWS service for given dates. Optional top_n."""
    start, end = parse_dates()

    top_n = request.args.get("top_n", default=10, type=int)

    data = cost_by_service(iso_date(start), iso_date(
        end), granularity='MONTHLY', top_n=top_n)
    return data


@cost_blueprint.route("/team_spend", methods=["GET"])  # Cant be used currently
def api_team_spend():
    """Cost breakdown by team/project (tag) for given dates. Requires ?tag_key=Team."""
    start, end = parse_dates()
    tag_key = request.args.get("tag_key", default="Team")
    top_n = request.args.get("top_n", default=10, type=int)

    data = cost_by_tag(iso_date(start), iso_date(
        end), tag_key=tag_key, granularity='MONTHLY', top_n=top_n)
    return jsonify(data)


@cost_blueprint.route("/anomalies", methods=["GET"])  # Cant be used currently
def api_anomalies():
    """Fetch anomalies in given period (default last 30 days)."""
    start, end = parse_dates()
    monitor_arn = request.args.get("monitor_arn")

    data = get_cost_anomalies(
        iso_date(start), iso_date(end), monitor_arn=monitor_arn)
    return jsonify(data)


@cost_blueprint.route("/forecast", methods=["GET"])  # ✅
def api_forecast():
    """Forecast spend for the given date range."""
    start, end = parse_dates()
    data = forecasted_spend(iso_date(start), iso_date(
        end), metric='UNBLENDED_COST', granularity='DAILY')
    return data


@cost_blueprint.route("/daily-cost", methods=["GET"])  # ✅
def daily_cost_trend():
    try:
        year = int(request.args.get("year"))
        month = int(request.args.get("month"))
        data = get_daily_cost_trend(year, month)
        return jsonify({"daily_costs": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
