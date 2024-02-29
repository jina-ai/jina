import os
from typing import Dict

DEPLOYMENT_FILES = [
    'statefulset-executor',
    'deployment-executor',
    'deployment-gateway',
    'deployment-uses-before',
    'deployment-uses-after',
    'deployment-uses-before-after',
]

cur_dir = os.path.dirname(__file__)
DEFAULT_RESOURCE_DIR = os.path.join(
    cur_dir, '..', '..', '..', '..', 'resources', 'k8s', 'template'
)


def get_yaml(template: str, params: Dict) -> Dict:
    """Create a resource on Kubernetes based on the `template`. It fills the `template` using the `params`.

    :param template: path to the template file.
    :param params: dictionary for replacing the placeholders (keys) with the actual values.
    :return: The yaml dictionary with the corresponding template filled with parameters
    """
    if template == 'configmap':
        yaml = _get_configmap_yaml(template, params)
    elif template in DEPLOYMENT_FILES:
        yaml = _get_yaml(template, params)
        if params.get('device_plugins'):
            yaml = _get_deployment_with_device_plugins(yaml, params)
        if params.get('env_from_secret'):
            yaml = _get_deployment_with_env_secret(yaml, params)
        if params.get('image_pull_secrets'):
            yaml = _get_deployment_with_image_pull_secrets(yaml, params)
    else:
        yaml = _get_yaml(template, params)

    return yaml


def _get_yaml(template: str, params: Dict) -> Dict:
    import yaml

    path = os.path.join(DEFAULT_RESOURCE_DIR, f'{template}.yml')

    with open(path, encoding='utf-8') as f:
        content = f.read()
        for k, v in params.items():
            content = content.replace(f'{{{k}}}', str(v))
        d = yaml.safe_load(content)

    return d


def _get_configmap_yaml(template: str, params: Dict):
    import yaml

    path = os.path.join(DEFAULT_RESOURCE_DIR, f'{template}.yml')

    with open(path, encoding='utf-8') as f:
        config_map = yaml.safe_load(f)

    config_map['metadata']['name'] = params.get('name') + '-' + 'configmap'
    config_map['metadata']['namespace'] = params.get('namespace')
    if params.get('data'):
        for key, value in params['data'].items():
            config_map['data'][key] = str(value)
    return config_map


def _get_device_plugins(params: Dict):
    data = {'limits': {}}
    for key, value in params.items():
        data['limits'][key] = value
    return data


def _get_deployment_with_device_plugins(deployment: Dict, params: Dict) -> Dict:
    device_plugins = _get_device_plugins(params['device_plugins'])

    deployment['spec']['template']['spec']['containers'][0][
        'resources'
    ] = device_plugins
    return deployment


def _get_deployment_with_env_secret(deployment: Dict, params: Dict) -> Dict:
    for k, v in params['env_from_secret'].items():
        env_var = {
            'name': k,
            'valueFrom': {'secretKeyRef': {'name': v['name'], 'key': v['key']}},
        }

        deployment['spec']['template']['spec']['containers'][0]['env'].append(env_var)

    return deployment


def _get_deployment_with_image_pull_secrets(deployment: Dict, params: Dict) -> Dict:
    image_pull_secrets = params['image_pull_secrets']
    image_pull_secrets_dict = [{'name': secret} for secret in image_pull_secrets]
    deployment['spec']['template']['spec']['imagePullSecrets'] = image_pull_secrets_dict
    return deployment
