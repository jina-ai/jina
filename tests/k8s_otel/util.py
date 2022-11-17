from typing import List, Dict


def parse_string_jaeger_tags(jaeger_tags: List) -> Dict[str, str]:
    """Parse jaeger tags into a dictionary"""
    return {i['key']: i['value'] for i in jaeger_tags if i['type'] == 'string'}
