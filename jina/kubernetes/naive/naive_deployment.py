import base64
from collections import defaultdict

from jina.hubble.helper import parse_hub_uri
from jina.hubble.hubio import HubIO
from jina.kubernetes import kubernetes_tools


def to_dns_name(name):
    return name.replace('/', '-')


def deploy_service(name, namespace, image_name, container_cmd, container_args, logger):
    logger.info(
        f'🔋\tCreate Service for "{name}" with image "{name}" pulling from "{image_name}"'
    )
    kubernetes_tools.create(
        'service',
        {
            'name': name,
            'target': name,
            'namespace': namespace,
            'port': 8081,
            'type': 'ClusterIP',
        },
    )

    cluster_ip = kubernetes_tools.get_service_cluster_ip(name, namespace)

    replicas = 1
    logger.info(f'🐳\tCreate Deployment for "{image_name}" with replicas {replicas}')
    kubernetes_tools.create(
        'deployment',
        {
            'name': name,
            'namespace': namespace,
            'image': image_name,
            'replicas': replicas,
            'command': container_cmd,
            'args': container_args,
            'port': 8081,
        },
    )
    return cluster_ip


def deploy_glue_executor(glue_executor, namespace, logger):
    return deploy_service(
        to_dns_name(glue_executor.name),
        namespace,
        'jinaai/jina',
        '["jina"]',
        f'["executor", "--uses", "{glue_executor.uses}", "--port-in", "8081", "--dynamic-routing-in", "--dynamic-routing-out"]',
        logger,
    )


def deploy(flow, deployment_type='k8s'):
    """Deploys the Flow. Currently only Kubernetes is supported.
    Each pod is deployed in a stateful set and we use zmq level communication.
    """

    if deployment_type == 'k8s':
        flow.logger.info(f'✨ Deploy Flow on Kubernetes...')
        namespace = flow.args.name
        flow.logger.info(f'📦\tCreate Namespace {namespace}')
        kubernetes_tools.create('namespace', {'name': namespace})

        pod_to_pea_and_args = defaultdict(list)
        for pod_name, pod in flow._pod_nodes.items():
            if pod_name == 'gateway':
                continue

            for name in ['head', 'tail']:
                if pod.peas_args[name] is not None:
                    cluster_ip = deploy_glue_executor(
                        pod.peas_args[name], namespace, flow.logger
                    )
                    pod_to_pea_and_args[pod_name].append(
                        [
                            pod.peas_args[name].name,
                            {'host_in': cluster_ip, 'parallel': pod.args.parallel},
                        ]
                    )

            scheme, name, tag, secret = parse_hub_uri(pod.args.uses)
            meta_data = HubIO.fetch_meta(name)
            image_name = meta_data.image_name

            # TODO handle compound pod
            for pea_arg in pod.peas_args['peas']:
                pea_name = pea_arg.name
                pea_dns_name = to_dns_name(pea_name)

                cluster_ip = deploy_service(
                    pea_dns_name,
                    namespace,
                    image_name,
                    container_cmd='["jina"]',
                    container_args='["executor", "--uses", "config.yml", "--port-in", "8081", "--dynamic-routing-in", "--dynamic-routing-out", "--socket-in", "ROUTER_BIND", "--socket-out", "ROUTER_BIND"]',
                    logger=flow.logger,
                )
                pod_to_pea_and_args[pod_name].append(
                    [pea_name, {'host_in': cluster_ip, 'parallel': pod.args.parallel}]
                )

        flow.logger.info(f'🔒\tCreate "gateway service"')
        external_gateway_service = 'gateway-exposed'
        kubernetes_tools.create(
            'service',
            {
                'name': external_gateway_service,
                'target': 'gateway',
                'namespace': namespace,
                'port': 8080,
                'type': 'ClusterIP',
            },
        )
        kubernetes_tools.create(
            'service',
            {
                'name': 'gateway-in',
                'target': 'gateway',
                'namespace': namespace,
                'port': 8081,
                'type': 'ClusterIP',
            },
        )

        # gateway_cluster_ip = kubernetes_tools.get_service_cluster_ip(
        #     'gateway-in', namespace
        # )

        gateway_yaml = create_gateway_yaml(
            pod_to_pea_and_args, 'gateway-in.f1.svc.cluster.local'
        )
        kubernetes_tools.create(
            'deployment',
            {
                'name': 'gateway',
                'replicas': 1,
                'port': 8080,
                'command': "[\"python\"]",
                'args': f"[\"gateway.py\", \"{gateway_yaml}\"]",
                'image': 'gcr.io/jina-showcase/generic-gateway',
                'namespace': namespace,
            },
        )

        # flow.logger.info(f'🌐\tCreate "Ingress resource"')
        # kubernetes_tools.create_gateway_ingress(namespace)
    else:
        raise Exception(f'deployment type "{deployment_type}" is not supported')


def create_gateway_yaml(pod_to_pea_and_args, gateway_host_in):
    yaml = f"""
        !Flow
        version: '1'
        with:
          port_expose: 8080
          host_in: {gateway_host_in}
          port_in: 8081
          protocol: http
        pods:
        """
    for pod_name, pea_to_args in pod_to_pea_and_args.items():
        peas_hosts = []
        for pea_dns_name, args in pea_to_args.items():
            peas_hosts.append(args['host_in'])

        yaml += f"""
          - name: {pod_name}
            port_in: 8081
            peas-hosts: ["{'", "'.join(peas_hosts)}"]
            external: True
            """

    # return yaml
    base_64_yaml = base64.b64encode(yaml.encode()).decode('utf8')
    return base_64_yaml
