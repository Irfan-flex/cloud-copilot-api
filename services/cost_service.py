import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from datetime import date, datetime, timedelta
import math

cost_explorer_client = boto3.client('ce')  # Cost Explorer


def iso_date(dt: date):
    """Return date string YYYY-MM-DD for datetime or date."""
    return dt.strftime('%Y-%m-%d')


def total_cost_trend(start_date, end_date, granularity='DAILY', metrics=('UnblendedCost',)):
    """
    Get total cost and time-series trend from Cost Explorer.
    - start_date, end_date: 'YYYY-MM-DD' strings (end is exclusive per API; usually set end = today)
    - granularity: 'DAILY'|'WEEKLY'|'MONTHLY'
    - metrics: tuple/list of metrics (e.g., 'UnblendedCost','BlendedCost','AmortizedCost','NetUnblendedCost')
    Returns: {'total': float, 'currency': str, 'series': [{'start':..., 'end':..., 'amount': float}, ...]}
    """
    try:
        resp = cost_explorer_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity=granularity,
            Metrics=list(metrics)
        )
    except ClientError as e:
        raise

    # Sum results (if there are groups the API returns groups; here we use ResultsByTime)
    series = []
    total = 0.0
    currency = None
    for item in resp.get('ResultsByTime', []):
        amt = 0.0
        # metric key: use first metric
        metric_name = metrics[0]
        amt_str = item.get('Total', {}).get(metric_name, {}).get('Amount')
        unit = item.get('Total', {}).get(metric_name, {}).get('Unit')
        if amt_str is not None:
            amt = float(amt_str)
            total += amt
            currency = unit
        series.append({
            'start': item.get('TimePeriod', {}).get('Start'),
            'end': item.get('TimePeriod', {}).get('End'),
            'amount': amt
        })
    return {'total': total, 'currency': currency, 'series': series}


def cost_by_service(start_date, end_date, granularity='MONTHLY', metric='UnblendedCost', top_n=None):
    """
    Return cost grouped by AWS service.
    - Returns list of {'service': name, 'amount': float, 'unit': str}
    - top_n: if provided, only returns top N (highest cost).
    """
    try:
        resp = cost_explorer_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity=granularity,
            Metrics=[metric],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
    except ClientError as e:
        raise

    # CostExplorer returns aggregated ResultsByTime; for monthly granularity we typically have one item
    agg = {}
    for timeblock in resp.get('ResultsByTime', []):
        for group in timeblock.get('Groups', []):
            key = group.get('Keys')[0]  # service name
            amt = float(group['Metrics'][metric]['Amount'])
            unit = group['Metrics'][metric]['Unit']
            agg.setdefault(key, 0.0)
            agg[key] += amt

    items = [{'service': k, 'amount': v, 'unit': unit} for k, v in agg.items()]
    items.sort(key=lambda x: x['amount'], reverse=True)
    if top_n:
        items = items[:top_n]
    return items


def cost_by_tag(start_date, end_date, tag_key, granularity='MONTHLY', metric='UnblendedCost', top_n=None):
    """
    Group costs by tag values for tag_key.
    - tag_key: string name of the tag key you activated (e.g., 'Project', 'Team', 'Owner')
    Returns: [{'tag_value': value_or_empty, 'amount': float, 'unit': str}, ...]
    """
    try:
        group = [{'Type': 'TAG', 'Key': tag_key}]
        resp = cost_explorer_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity=granularity,
            Metrics=[metric],
            GroupBy=group
        )
    except ClientError as e:
        raise

    agg = {}
    unit = None
    for timeblock in resp.get('ResultsByTime', []):
        for group in timeblock.get('Groups', []):
            # group['Keys'] contains the tag value(s)
            tag_value = group['Keys'][0] if group['Keys'] else ''
            amt = float(group['Metrics'][metric]['Amount'])
            unit = group['Metrics'][metric]['Unit']
            agg.setdefault(tag_value, 0.0)
            agg[tag_value] += amt

    items = [{'tag_value': k, 'amount': v, 'unit': unit}
             for k, v in agg.items()]
    items.sort(key=lambda x: x['amount'], reverse=True)
    if top_n:
        items = items[:top_n]
    return items


def top_n_services(start_date, end_date, n=5, metric='UnblendedCost'):
    """Return top-n services by spend in the given period."""
    return cost_by_service(start_date, end_date, granularity='MONTHLY', metric=metric, top_n=n)


def get_cost_anomalies(start_date, end_date, monitor_arn=None):
    """
    Fetch anomalies detected in the given time window.
    - If monitor_arn is provided, only anomalies for that monitor will be returned.
    Returns a list of anomalies with fields like: { 'AnomalyId','AnomalyStartDate','AnomalyEndDate','TotalImpact','DimensionValue', ... }
    """
    params = {
        'TimePeriod': {'Start': start_date, 'End': end_date},
        'MaxResults': 100
    }
    if monitor_arn:
        params['MonitorArn'] = monitor_arn

    try:
        resp = cost_explorer_client.get_anomalies(**params)
    except ClientError as e:
        raise

    anomalies = []
    for a in resp.get('Anomalies', []):
        anomalies.append({
            'id': a.get('AnomalyId'),
            'start': a.get('AnomalyStartDate'),
            'end': a.get('AnomalyEndDate'),
            'dimension': a.get('DimensionValue'),
            'root_causes': a.get('RootCauses'),
            'total_estimated_impact': a.get('TotalImpact'),
            'severity': a.get('Severity')
        })
    return anomalies


def get_cost_data():
    sts = boto3.client('sts')

    end = datetime.today().date()
    start = end - timedelta(days=30)

    # Get AWS Account ID
    account_id = sts.get_caller_identity()['Account']

    # Get cost data grouped by service
    response = cost_explorer_client.get_cost_and_usage(
        TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    results = []
    total_cost = 0.0

    for day in response['ResultsByTime']:
        for group in day['Groups']:
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            total_cost += cost
            results.append({
                'date': day['TimePeriod']['Start'],
                'service': group['Keys'][0],
                'cost': cost
            })

    return {
        'data': results,
        'total_cost': total_cost,
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'account_id': account_id
    }


def forecasted_spend(start_date, end_date, metric='UNBLENDED_COST', granularity='DAILY'):
    """
    Get Cost Explorer forecast for the given time window.
    - start_date/end_date: forecast range (Start inclusive, End exclusive)
    - metric: 'BLENDED_COST'|'UNBLENDED_COST'|'AMORTIZED_COST'|'USAGE_QUANTITY' etc.
    - granularity: 'DAILY' or 'MONTHLY'
    Returns: {'forecast_result': [{'timestamp':..., 'mean':float,'lower':float,'upper':float}, ...], 'unit': str}
    """
    try:
        resp = cost_explorer_client.get_cost_forecast(
            TimePeriod={'Start': start_date, 'End': end_date},
            Metric=metric,
            Granularity=granularity
        )
    except ClientError as e:
        raise

    unit = resp.get('ForecastResultsByTime', [{}])[0].get('MeanValue', None)
    series = []
    for item in resp.get('ForecastResultsByTime', []):
        series.append({
            'time_period_start': item['TimePeriod']['Start'],
            'time_period_end': item['TimePeriod']['End'],
            'mean': float(item.get('MeanValue', 0.0)),
            'lower': float(item.get('PredictionIntervalLowerBound', 0.0)),
            'upper': float(item.get('PredictionIntervalUpperBound', 0.0))
        })
    # Unit is in resp['ForecastResultsByTime'][0]['Unit'] typically
    unit = resp.get('ForecastResultsByTime', [{}])[0].get('Unit')
    return {'series': series, 'unit': unit}


def cost_service_and_tag(start_date, end_date, tag_key, granularity='MONTHLY', metric='UnblendedCost'):
    """
    Group cost by service and tag value (two-level grouping).
    Returns a dict: { service_name: [ {tag_value:..., amount:...}, ... ], ... }
    """
    groups = [
        {'Type': 'DIMENSION', 'Key': 'SERVICE'},
        {'Type': 'TAG', 'Key': tag_key}
    ]
    resp = cost_explorer_client.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity=granularity,
        Metrics=[metric],
        GroupBy=groups
    )
    result = {}
    for timeblock in resp.get('ResultsByTime', []):
        for g in timeblock.get('Groups', []):
            keys = g.get('Keys', [])
            service = keys[0] if len(keys) > 0 else 'Unknown'
            tag_value = keys[1] if len(keys) > 1 else ''
            amt = float(g['Metrics'][metric]['Amount'])
            result.setdefault(service, {})
            result[service].setdefault(tag_value, 0.0)
            result[service][tag_value] += amt

    # Convert nested dict to structured
    out = {svc: [{'tag_value': tv, 'amount': amt}
                 for tv, amt in vals.items()] for svc, vals in result.items()}
    return out


def get_daily_cost_trend(year: int, month: int):
    """
    Returns daily AWS cost trend for a given month.
    Example: get_daily_cost_trend(2025, 9) → daily costs for Sept 2025
    """
    # Get first and last day of the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    response = cost_explorer_client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.strftime("%Y-%m-%d"),
            # CE is exclusive of End
            "End": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"]
    )

    daily_costs = []
    for result in response["ResultsByTime"]:
        day = result["TimePeriod"]["Start"]
        amount = float(result["Total"]["UnblendedCost"]["Amount"])
        daily_costs.append({
            "date": day,
            "cost": amount
        })

    return daily_costs


def list_active_cost_allocation_tags():
    """
    Returns all active cost allocation tag keys in your account.
    """
    response = cost_explorer_client.list_cost_allocation_tags(
        Status='Active'  # Only tags that are enabled for cost allocation
    )
    tags = response.get('CostAllocationTags', [])
    return tags


def tag_exists(tag_key, start_date, end_date):
    """
    Check if a tag key exists in Cost Explorer data by fetching tag values.
    Returns True if tag has any values in the given time range.
    """
    try:
        response = cost_explorer_client.get_tags(
            TimePeriod={'Start': iso_date(
                start_date), 'End': iso_date(end_date)},
            TagKey=tag_key,
            MaxResults=5  # we just need to see if values exist
        )
        values = response.get("Tags", [])
        return len(values) > 0
    except Exception as e:
        return False


# def cost_by_tag(start_date, end_date, tag_key):
#     # tags = get_active_tags()
#     # if tag_key not in tags:
#     #     return {"error": f"No active cost allocation tag found for '{tag_key}'."}
#     # if not tag_exists(tag_key, start_date, end_date):
#     #     return {"error": f"Tag '{tag_key}' not found in cost data."}

#     response = cost_explorer_client.get_cost_and_usage(
#         TimePeriod={'Start': iso_date(start_date), 'End': iso_date(end_date)},
#         Granularity='MONTHLY',
#         Metrics=['UnblendedCost'],
#         GroupBy=[{'Type': 'TAG', 'Key': tag_key}]
#     )
#     result = []
#     for group in response['ResultsByTime'][0]['Groups']:
#         key = group['Keys'][0]
#         cost = float(group['Metrics']['UnblendedCost']['Amount'])
#         result.append({'tag_value': key, 'cost': cost})
#     return result

def cost_by_tag(start_date, end_date, tag_key):
    response = cost_explorer_client.get_cost_and_usage(
        TimePeriod={'Start': iso_date(start_date), 'End': iso_date(end_date)},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'TAG', 'Key': tag_key}]
    )

    tag_costs = {}

    # loop through each time period (each month/week depending on granularity)
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            key = group['Keys'][0] or "UnTagged"
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            tag_costs[key] = tag_costs.get(key, 0.0) + cost

    if not tag_costs:
        return {"error": f"Tag '{tag_key}' not found in cost data."}

    # convert to list of dicts
    result = [{'tag_value': k, 'cost': v} for k, v in tag_costs.items()]
    return result
