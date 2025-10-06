from typing import Dict, List
import boto3

compute_optimizer_client = boto3.client('compute-optimizer', region_name="us-east-1")
cost_explorer_client = boto3.client('ce', region_name="us-east-1")  # Cost Explorer
ec2 = boto3.client('ec2', region_name='us-east-1')

# AWS public IPv4 charge (USD/hour) effective Feb 1, 2024
USD_PER_IP_PER_HOUR = 0.005


def get_ec2_rightsizing_recommendations():
    results = []

    try:
        response = compute_optimizer_client.get_ec2_instance_recommendations()
        recs = response.get("instanceRecommendations", [])

        for rec in recs:
            finding = rec.get("finding", "Optimized")
            if finding == "Optimized":
                continue  # skip already optimized instances

            instance_id = rec.get("instanceArn", "").split("/")[-1]
            current_type = rec.get("currentInstanceType")
            options = rec.get("recommendationOptions", [])
            if not options:
                continue

            best_option = options[0]
            recommended_type = best_option.get("instanceType")
            monthly_saving_usd = best_option.get(
                "estimatedMonthlySavings", {}).get("value", 0)

            if monthly_saving_usd <= 0:
                continue  # skip zero savings

            action = "Downsize" if finding == "Overprovisioned" else "Upsize"

            results.append({
                "InstanceId": instance_id,
                "CurrentType": current_type,
                "RecommendedType": recommended_type,
                "Action": action,
                "MonthlySavingsUSD": round(monthly_saving_usd, 2)
            })

        return results or [{"info": "No rightsizing recommendations found"}]

    except Exception as e:
        return [{"error": str(e)}]


# def get_ebs_rightsizing_recommendations():
#     try:
#         response = compute_optimizer_client.get_ebs_volume_recommendations()
#         return response.get("volumeRecommendations", [])
#     except Exception as e:
#         return [{'error': str(e)}]

def get_ebs_rightsizing_recommendations():
    results = []

    try:
        response = compute_optimizer_client.get_ebs_volume_recommendations()
        recs = response.get("volumeRecommendations", [])

        for rec in recs:
            volume_arn = rec.get("volumeArn", "")
            volume_id = volume_arn.split(
                "/")[-1] if "/" in volume_arn else volume_arn
            current_type = rec.get(
                "currentConfiguration", {}).get("volumeType")

            options = rec.get("recommendationOptions", [])
            if not options:
                continue

            best_option = options[0]
            recommended_type = best_option.get(
                "configuration", {}).get("volumeType")

            # Estimated monthly savings (USD)
            monthly_saving_usd = best_option.get(
                "estimatedMonthlySavings", {}).get("value", 0)
            monthly_saving_inr = round(monthly_saving_usd, 2)

            # Always “Migrate” since EBS optimization means changing type
            results.append({
                "VolumeId": volume_id,
                "CurrentType": current_type,
                "RecommendedType": recommended_type,
                "Action": "Migrate",
                "MonthlySavingsINR": monthly_saving_inr
            })

        return results or [{"info": "No EBS rightsizing recommendations found"}]

    except Exception as e:
        return [{"error": str(e)}]


def get_unattached_ebs_volumes(region='us-east-1'):
    volumes = ec2.describe_volumes(
        Filters=[{'Name': 'status', 'Values': ['available']}])
    return [v['VolumeId'] for v in volumes['Volumes']]


def get_unassociated_elastic_ips(region='us-east-1'):
    addresses = ec2.describe_addresses()
    unattached_eips = [a['PublicIp']
                       for a in addresses['Addresses'] if 'InstanceId' not in a]
    return {"unattached_eips": unattached_eips, "cost_savings": eip_cost_estimate(unattached_eips)}


def get_inactive_nat_gateways(region='us-east-1'):
    nats = ec2.describe_nat_gateways(
        Filters=[{'Name': 'state', 'Values': ['available', 'pending']}])
    return [nat['NatGatewayId'] for nat in nats['NatGateways'] if nat['State'] != 'available']


def get_reserved_instance_savings_opportunities(service='Amazon Elastic Compute Cloud - Compute'):
    try:
        response = cost_explorer_client.get_reservation_purchase_recommendation(
            Service=service,
            AccountScope='LINKED',  # or 'LINKED' if using single account
            LookbackPeriodInDays='SEVEN_DAYS',
            TermInYears='ONE_YEAR',
            PaymentOption='ALL_UPFRONT'
        )
        recommendations = response.get('Recommendations', [])
        results = []

        for rec in recommendations:
            summary = rec.get("RecommendationSummary", {})
            currency = summary.get("CurrencyCode", "USD")
            estimated_savings = float(summary.get(
                "EstimatedMonthlySavingsAmount", 0))
            results.append({
                "Service": service,
                "EstimatedMonthlySavingsINR": round(estimated_savings * 83, 2),
                "EstimatedSavingsPercent": summary.get("EstimatedSavingsPercentage", 0),
                "Currency": currency
            })

        return results or [{"info": "No RI purchase recommendations found"}]
    except Exception as e:
        return [{"error": str(e)}]


def get_savings_plans_opportunities():
    try:
        response = cost_explorer_client.get_savings_plans_purchase_recommendation(
            SavingsPlansType='COMPUTE_SP',
            TermInYears='ONE_YEAR',
            PaymentOption='ALL_UPFRONT',
            LookbackPeriodInDays='SEVEN_DAYS'
        )

        recommendations = response.get(
            "SavingsPlansPurchaseRecommendation", {}
        ).get("SavingsPlansPurchaseRecommendationDetails", [])

        concise_data = []

        for rec in recommendations:
            current_cost = float(rec.get("EstimatedOnDemandCost", 0))
            full_savings = float(rec.get("EstimatedMonthlySavingsAmount", 0))
            savings_percent = round(
                float(rec.get("EstimatedSavingsPercentage", 0)), 2)
            action = f"Buy 1-year {rec.get('PaymentOption', 'All Upfront')} Compute Savings Plan"

            if full_savings <= 0:
                continue  # ignore zero or negative savings

            # Estimate savings based on current usage
            # Assuming savings % is roughly proportional to usage
            realistic_savings = round(
                current_cost * (savings_percent / 100), 2)
            service_type = rec.get("SavingsPlansType", "COMPUTE_SP")
            if service_type == "EC2_INSTANCE_SP":
                service_name = "EC2"
            elif service_type == "COMPUTE_SP":
                service_name = "Compute (EC2/Fargate/Lambda)"
            elif service_type == "SAGEMAKER_SP":
                service_name = "SageMaker"
            else:
                service_name = service_type
            concise_data.append({
                "Service": service_name,
                "CurrentMonthlyCostUSD": round(current_cost, 2),
                "EstimatedSavingsFullUtilizationUSD": round(full_savings, 2),
                "EstimatedSavingsBasedOnCurrentUsageUSD": realistic_savings,
                "SavingsPercentage": f"{savings_percent}%",
                "Action": action,
                "Note": "Full savings assumes consistent usage; realistic savings based on current usage."
            })

        return concise_data or [{"info": "No meaningful savings recommendations found"}]

    except Exception as e:
        return [{"error": str(e)}]


def get_ec2_instances_without_tags(region='us-east-1'):
    instances = ec2.describe_instances()
    untagged = []
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            if 'Tags' not in instance or len(instance['Tags']) == 0:
                untagged.append(instance['InstanceId'])
    return untagged


def eip_cost_estimate(
    eip_list: List[str],
    usd_per_ip_per_hour: float = USD_PER_IP_PER_HOUR,
    days_in_month: int = 30,
    usd_to_inr: float = 83.0
) -> Dict[str, float]:
    """
    Returns estimated monthly & yearly cost for the provided (idle/unattached) EIPs.
    - eip_list: list of IP strings
    - usd_per_ip_per_hour: AWS charge (default $0.005/hr)
    - days_in_month: use 30 by default (adjust if you want calendar month)
    - usd_to_inr: conversion rate to INR (supply live rate if you want accuracy)
    """
    count = len(eip_list)
    hours_per_month = 24 * days_in_month

    monthly_usd_per_ip = usd_per_ip_per_hour * hours_per_month
    monthly_usd_total = monthly_usd_per_ip * count
    yearly_usd_total = monthly_usd_total * 12

    return {
        "ip_count": count,
        "monthly_usd_per_ip": round(monthly_usd_per_ip, 4),
        "monthly_usd_total": round(monthly_usd_total, 4),
        "yearly_usd_total": round(yearly_usd_total, 4),
        "assumptions": {
            "usd_per_ip_per_hour": usd_per_ip_per_hour,
            "days_in_month": days_in_month,
        }
    }


# print(get_reserved_instance_savings_opportunities(
#     'Amazon Relational Database Service'))
