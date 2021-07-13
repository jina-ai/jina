import time

from kubernetes import client, config, utils
import os
import tempfile

from kubernetes.utils import FailToCreateError

config.load_kube_config()
k8s_client = client.ApiClient()
v1 = client.CoreV1Api()
beta = client.ExtensionsV1beta1Api()

def create(template, params):
    yaml = get_yaml(template, params)
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as tmp:
            # do stuff with temp file
            tmp.write(yaml)
        # try:
        #     if template == 'service':
        #         pass
        #         # v1.delete_namespaced_service(params['name'].lower(), 'default')
        #         # time.sleep(10)
        #     elif template == 'deployment':
        #         beta.delete_namespaced_deployment(params['name'].lower(), 'default')
        # except:
        #     pass

        try:
            utils.create_from_yaml(k8s_client, path)
        except FailToCreateError as e:
            if e.api_exceptions[0].status == 409:
                print('exists already')
            else:
                raise e
    finally:
        os.remove(path)


def get_yaml(template, params):
    with open(f'jina/kubernetes/template/{template}.yml') as f:
        content = f.read()
        for k, v in params.items():
            content = content.replace(f'{{{k}}}', str(v))
    return content


def get_service_cluster_ip(service_name, namespace):
    resp = v1.read_namespaced_service(service_name, namespace)
    return resp.spec.cluster_ip

def get_service_spec(service_name, namespace):
    resp = v1.read_namespaced_service(service_name, namespace)
    return resp.spec