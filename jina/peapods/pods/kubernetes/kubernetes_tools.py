import threading
import time

from bcolors import UNDERLINE, ENDC, BOLD, PASS


from kubernetes import client, config, utils
import os
import tempfile

from kubernetes.utils import FailToCreateError
from kubernetes.watch import Watch

config.load_kube_config()
k8s_client = client.ApiClient()
v1 = client.CoreV1Api()
beta = client.ExtensionsV1beta1Api()
networking_v1_beta1_api = client.NetworkingV1beta1Api()


def create_gateway_ingress(namespace: str):
    # create ingress class
    # body = client.V1beta1IngressClass(
    #     api_version="networking.k8s.io/v1",
    #     kind="IngressClass",
    #     metadata=client.V1ObjectMeta(
    #         name=f'{namespace}-lb',
    #         annotations= {
    #             "linkerd.io/inject": "enabled"
    #         }
    #     ),
    #     spec=client.V1beta1IngressClassSpec(
    #         controller="example.com/ingress-controller",
    #         parameters={
    #             "apiGroup": "k8s.example.com",
    #             "kind": "IngressParameters",
    #             "name": "external-lb",
    #         }
    #     )
    # )
    # networking_v1_beta1_api.create_ingress_class(
    #     body=body
    # )

    # create ingress
    body = client.NetworkingV1beta1Ingress(
        api_version="networking.k8s.io/v1beta1",
        kind="Ingress",
        metadata=client.V1ObjectMeta(
            name=f'{namespace}-ingress',
            annotations={
                "nginx.ingress.kubernetes.io/rewrite-target": "/",
                # "linkerd.io/inject": "enabled",
            },
        ),
        spec=client.NetworkingV1beta1IngressSpec(
            rules=[
                client.NetworkingV1beta1IngressRule(
                    host="",
                    http=client.NetworkingV1beta1HTTPIngressRuleValue(
                        paths=[
                            client.NetworkingV1beta1HTTPIngressPath(
                                path="/",
                                backend=client.NetworkingV1beta1IngressBackend(
                                    service_port=8080, service_name="gateway-exposed"
                                ),
                            )
                        ]
                    ),
                )
            ]
        ),
    )
    # Creation of the Deployment in specified namespace
    # (Can replace "default" with a namespace you may have created)
    networking_v1_beta1_api.create_namespaced_ingress(namespace=namespace, body=body)


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
        except Exception as e2:
            raise e2
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


def log_in_thread(pod_name, namespace, container):
    pod = v1.read_namespaced_pod(pod_name, namespace)
    containers = [container.name for container in pod.spec.containers]
    if container not in containers:
        return
    w = Watch()
    for e in w.stream(
        v1.read_namespaced_pod_log,
        name=pod_name,
        namespace=namespace,
        container=container,
    ):
        print(f"{UNDERLINE}{BOLD}{PASS}{pod_name}:{container}{ENDC} =>", e)


def get_pod_logs(namespace):
    pods = v1.list_namespaced_pod(namespace)
    pod_names = [item.metadata.name for item in pods.items]
    for pod_name in pod_names:
        for container in [
            'executor',
            'istio-proxy',
            'dumper-init',
        ]:  # , 'linkerd-proxy']:
            x = threading.Thread(
                target=log_in_thread, args=(pod_name, namespace, container)
            )
            x.start()
            time.sleep(0.25)  # wait to get the logs after another
