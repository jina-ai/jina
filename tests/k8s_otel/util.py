from typing import Dict, List

import requests

HEALTH_CHECK_OP = '%2Fgrpc.health.v1.Health%2FCheck'


def parse_string_jaeger_tags(jaeger_tags: List) -> Dict[str, str]:
    """Parse jaeger tags into a dictionary"""
    return {i['key']: i['value'] for i in jaeger_tags if i['type'] == 'string'}


def get_last_health_check_data(jaeger_port: int, service_name: str) -> dict:
    """Get most recent health check data from Jaeger API for a given service

    Args:
        jaeger_port: Port to forward to Jaeger API
        service_name: Service to get health check data for
    Returns:
        Health check trace JSON (dict)
    """
    return requests.get(
        f'http://localhost:{jaeger_port}/api/traces?service={service_name}&limit=1&operation={HEALTH_CHECK_OP}'
    ).json()['data'][0]
