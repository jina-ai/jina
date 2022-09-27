from typing import Dict


def get_metric_values(raw_metrics: str) -> Dict[str, float]:
    """
    get the value of a metric from the prometheus endpoint
    :param raw_metrics: raw string coming from scrapping the http prometheus endpoint
    :return: Dictionary which full metrics name as key and the corresponding value
    """
    metrics = dict()

    for line in raw_metrics.split('\n'):
        if not line.startswith('#') and ' ' in line:
            line_split = line.split(' ')

            metric_name = ''.join(line_split[0:-1])

            metric_value = float(line_split[-1])

            metrics[metric_name] = metric_value

    return metrics
