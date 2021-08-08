import base64
from collections import defaultdict

from jina.hubble.helper import parse_hub_uri
from jina.hubble.hubio import HubIO

from jina.peapods import BasePod, Pod

IS_LOCAL = False

if IS_LOCAL:
    gateway_image = 'generic-gateway'
else:
    gateway_image = 'gcr.io/jina-showcase/generic-gateway:latest'


def to_dns_name(name):
    return name.replace('/', '-')


def deploy_service(
    name,
    namespace,
    port_in,
    port_out,
    port_ctrl,
    port_expose,
    image_name,
    container_cmd,
    container_args,
    logger,
    init_container=None,
):
    from jina.kubernetes import kubernetes_tools

    logger.info(
        f'🔋\tCreate Service for "{name}" with image "{name}" pulling from "{image_name}" \ncontainer_cmd: {container_cmd}\n{name} container_args: {container_args}'
    )
    kubernetes_tools.create(
        'service',
        {
            'name': name,
            'target': name,
            'namespace': namespace,
            'port_in': port_in,
            'port_out': port_out,
            'port_ctrl': port_ctrl,
            'port_expose': port_expose,
            'type': 'ClusterIP',
        },
    )

    # cluster_ip = kubernetes_tools.get_service_cluster_ip(name, namespace)

    replicas = 1
    logger.info(
        f'🐳\tCreate Deployment for "{image_name}" with replicas {replicas} and init_container {init_container is not None}'
    )
    if init_container:
        kubernetes_tools.create(
            'deployment-init',
            {
                'name': name,
                'namespace': namespace,
                'image': image_name,
                'replicas': replicas,
                'command': container_cmd,
                'args': container_args,
                'port_in': port_in,
                'port_out': port_out,
                'port_ctrl': port_ctrl,
                'port_expose': port_expose,
                **init_container,
            },
        )
    else:
        kubernetes_tools.create(
            'deployment',
            {
                'name': name,
                'namespace': namespace,
                'image': image_name,
                'replicas': replicas,
                'command': container_cmd,
                'args': container_args,
                'port_in': port_in,
                'port_out': port_out,
                'port_ctrl': port_ctrl,
                'port_expose': port_expose,
            },
        )
    return f'{name}.{namespace}.svc.cluster.local'


def deploy_glue_executor(glue_executor, namespace, logger):
    if glue_executor.uses == 'gcr.io/jina-showcase/match-merger':
        return deploy_service(
            to_dns_name(glue_executor.name),
            namespace,
            glue_executor.port_in,
            glue_executor.port_out,
            glue_executor.port_ctrl,
            glue_executor.port_expose,
            glue_executor.uses,
            '["jina"]',
            f'["executor", "--uses", "config.yml", {get_cli_params(glue_executor)}]',
            logger,
        )
    else:
        return deploy_service(
            to_dns_name(glue_executor.name),
            namespace,
            glue_executor.port_in,
            glue_executor.port_out,
            glue_executor.port_ctrl,
            glue_executor.port_expose,
            # 'jinaai/jina',
            'gcr.io/jina-showcase/generic-gateway:latest',
            '["jina"]',
            f'["executor", "--uses", "{glue_executor.uses}", {get_cli_params(glue_executor)}]',
            logger,
        )


# def get_cli_params(arguments):
#     cli_args = [f'"--{name}", "' + repr(
#         str(getattr(arguments, name.replace('-', '_')))
#     ).replace('\'', '').replace('"', '\\"') + '"'
#                 for name in [
#                     'port-in',
#                     'port-out',
#                     'port-ctrl',
#                     'port-expose',
#                     'host-in',
#                     'host-out',
#                     'socket-in',
#                     'socket-out',
#                     'pea-id',
#                     'polling',
#                     'scheduling',
#                     'pea-role',
#                     'pod-role',
#                     # 'zmq-identity',
#                     'workspace-id',
#                     'name',
#                     'identity',
#                     # 'hosts-in-connect',
#                     # 'upload-files',
#                     'num-part',
#                     'parallel',
#                     'protocol',
#                     'routing-table',
#                     'runtime-cls',
#                     'runtime-backend',
#                     'prefetch-on-recv',
#                     'prefetch',
#                     'ctrl-with-ipc'
#                 ]
#                 if hasattr(arguments, name.replace('-', '_'))]
#
#     for name in ['dynamic-routing-in', 'dynamic-routing-out']:
#         if getattr(arguments, name.replace('-', '_')):
#             cli_args.append(f'"--{name}"')
#     cli_string = ', '.join(cli_args)
#     return cli_string


def get_cli_params(arguments):
    skip_attributes = ['workspace', 'log_config', 'uses']
    arg_list = [
        [attribute, attribute.replace('_', '-'), value]
        for attribute, value in arguments.__dict__.items()
    ]
    cli_args = []
    for attribute, cli_attribute, value in arg_list:
        if attribute in skip_attributes:
            continue
        if type(value) == bool and value:
            cli_args.append(f'"--{cli_attribute}"')
        else:
            if value:
                value = str(value)
                value = value.replace('\'', '').replace('"', '\\"')
                cli_args.append(f'"--{cli_attribute}", "{value}"')
    cli_string = ', '.join(cli_args)
    return cli_string


def get_image_name(uses):
    try:
        scheme, name, tag, secret = parse_hub_uri(uses)
        meta_data = HubIO.fetch_meta(name)
        image_name = meta_data.image_name
        return image_name
    except Exception:
        return uses.replace('docker://', '')


def prepare_flow(flow):
    namespace = flow.args.name
    flow.args.host = f'gateway.{namespace}.svc.cluster.local'
    flow.host = f'gateway.{namespace}.svc.cluster.local'

    for pod_name, pod in flow._pod_nodes.items():
        service_name = to_dns_name(pod.args.name)
        if pod.args.parallel > 1:

            pod.args.peas_hosts = [
                f'{service_name}-head.{namespace}.svc.cluster.local',
                f'{service_name}-tail.{namespace}.svc.cluster.local',
            ] + [
                f'{service_name}-pea-{i}.{namespace}.svc.cluster.local'
                for i in range(pod.args.parallel)
            ]
            for pea_arg in pod.peas_args['peas']:
                pea_arg.host_in = pod.args.peas_hosts[0]
                pea_arg.host_out = pod.args.peas_hosts[1]

            # pod.host = f'{service_name}-head.{namespace}.svc.cluster.local'
            # pod.head_host = f'{service_name}-head.{namespace}.svc.cluster.local'
        # else:
        # pod.host = f'{service_name}.{namespace}.svc.cluster.local'
        # pod.head_host = f'{service_name}.{namespace}.svc.cluster.local'

    return flow.build(copy_flow=True)


def deploy(flow, deployment_type='k8s'):
    """Deploys the Flow. Currently only Kubernetes is supported.
    Each pod is deployed in a stateful set and we use zmq level communication.
    """
    from jina.kubernetes import kubernetes_tools

    flow = prepare_flow(flow)

    if deployment_type == 'k8s':
        flow.logger.info(f'✨ Deploy Flow on Kubernetes...')
        namespace = flow.args.name
        flow.logger.info(f'📦\tCreate Namespace {namespace}')
        kubernetes_tools.create('namespace', {'name': namespace})

        # pod_to_pea_and_args = defaultdict(list)
        for pod_name, pod in flow._pod_nodes.items():
            if pod_name == 'gateway':
                continue
            # if type(pod).__name__ == 'CompoundPod':
            #     pod = Pod(pod.replicas_args)
            #     replicas = pod.args.replicas
            # else:
            #     replicas = 1
            for name in ['head', 'tail']:
                if pod.peas_args[name] is not None:
                    cluster_ip = deploy_glue_executor(
                        pod.peas_args[name],
                        namespace,
                        flow.logger,
                    )
                    # pod_to_pea_and_args[pod_name].append(
                    #     [
                    #         pod.peas_args[name].name,
                    #         pod.head_port_in,
                    #         {
                    #             'host_in': cluster_ip,
                    #             'parallel': pod.args.parallel,
                    #             'needs': pod.needs,
                    #         },
                    #     ]
                    # )

            image_name = get_image_name(pod.args.uses)

            # TODO handle compound pod
            for pea_arg in pod.peas_args['peas']:
                pea_name = pea_arg.name
                pea_dns_name = to_dns_name(pea_name)

                if pod.args.uses == 'jinahub+docker://AnnoySearcher':
                    shards = len(pod.peas_args['peas'])
                    init_image_name = get_image_name(
                        'jinahub+docker://PostgreSQLStorage'
                    )
                    postgres_cluster_ip = "10.3.255.243"

                    python_script = (
                        'import os; '
                        'os.chdir(\'/\'); '
                        'from workspace import PostgreSQLStorage; '
                        'storage = PostgreSQLStorage('
                        f'hostname="{postgres_cluster_ip}",'
                        'port=5432,'
                        'username="postgresadmin",'
                        'password="1235813",'
                        'database="postgresdb",'
                        f'table="{pod_name}",'
                        '); '
                        'storage.dump(parameters={'
                        '"dump_path": "/shared", '
                        f'"shards": {shards}'
                        '});'
                    ).replace("\"", "\\\"")

                    init_container = {
                        'init-name': 'dumper-init',
                        'init-image': init_image_name,
                        'init-command': '["python", "-c", "' + python_script + '"]',
                    }
                    print('init-container')
                    # initContainers:
                    # - name: init - myservice
                    # image: busybox:1.28
                    # command: ['sh', '-c',
                    #           "until nslookup myservice.$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace).svc.cluster.local; do echo waiting for myservice; sleep 2; done"]
                else:
                    init_container = None

                double_quote = '"'
                uses_with = (
                    pea_arg.uses_with.__str__().replace("'", "\\\"")
                    if pea_arg.uses_with
                    else None
                )
                uses_metas = {'pea_id': pea_arg.pea_id}.__str__().replace("'", "\\\"")

                cluster_ip = deploy_service(
                    pea_dns_name,
                    namespace,
                    pea_arg.port_in,
                    pea_arg.port_out,
                    pea_arg.port_ctrl,
                    pea_arg.port_expose,
                    image_name,
                    container_cmd='["jina"]',
                    container_args=f'["executor", '
                    f'"--uses", "config.yml", '
                    f'"--override-metas", "{uses_metas}", '
                    f'{f"{double_quote}--override-with{double_quote}, {double_quote}{uses_with}{double_quote}, " if pea_arg.uses_with else ""} '
                    f'{get_cli_params(pea_arg)}]',
                    logger=flow.logger,
                    init_container=init_container,
                )

                # pod_to_pea_and_args[pod_name].append(
                #     [
                #         pea_name,
                #         pod.head_port_in,
                #         {
                #             'host_in': cluster_ip,
                #             'parallel': pod.args.parallel,
                #             'needs': pod.needs,
                #         },
                #     ]
                # )

        # flow.logger.info(f'🔒\tCreate "gateway service"')
        # external_gateway_service = 'gateway-exposed'
        # kubernetes_tools.create(
        #     'service',
        #     {
        #         'name': external_gateway_service,
        #         'target': 'gateway',
        #         'namespace': namespace,
        #         'port_in': 8080,
        #         'port_out': 8888,
        #         'port_ctrl': 9999,
        #         'type': 'ClusterIP',
        #     },
        # )

        # kubernetes_tools.create(
        #     'service',
        #     {
        #         'name': 'gateway-in',
        #         'target': 'gateway',
        #         'namespace': namespace,
        #         'port_in': flow._pod_nodes['gateway'].args.port_in,
        #         'port_out': flow._pod_nodes['gateway'].args.port_out,
        #         'port_ctrl': flow._pod_nodes['gateway'].args.port_ctrl,
        #         'type': 'ClusterIP',
        #     },
        # )

        gateway_args = flow._pod_nodes['gateway'].peas_args['peas'][0]
        deploy_service(
            gateway_args.name,
            namespace,
            gateway_args.port_in,
            gateway_args.port_out,
            gateway_args.port_ctrl,
            gateway_args.port_expose,
            'gcr.io/jina-showcase/generic-gateway:latest',
            container_cmd='["jina"]',
            container_args=f'["gateway", ' f'{get_cli_params(gateway_args)}]',
            logger=flow.logger,
            init_container=None,
        )

        # gateway_cluster_ip = kubernetes_tools.get_service_cluster_ip(
        #     'gateway-in', namespace
        # )

        # gateway_yaml = create_gateway_yaml(
        #     pod_to_pea_and_args,
        #     f'gateway-in.{flow.args.name}.svc.cluster.local',
        #     flow._pod_nodes['gateway'].args.port_in
        # )

        # kubernetes_tools.create(
        #     'deployment',
        #     {
        #         'name': 'gateway',
        #         'replicas': 1,
        #         'port_in': 8080,
        #         'port_out': 8888,
        #         'port_ctrl': 9999,
        #         'command': "[\"python\"]",
        #         'args': f"[\"gateway.py\", \"{gateway_yaml}\"]",
        #         'image': gateway_image,
        #         'namespace': namespace,
        #     },
        # )

        # flow.logger.info(f'🌐\tCreate "Ingress resource"')
        # kubernetes_tools.create_gateway_ingress(namespace)
    else:
        raise Exception(f'deployment type "{deployment_type}" is not supported')


# def create_gateway_yaml(pod_to_pea_and_args, gateway_host_in, gateway_port_in):
#     yaml = f"""
#         !Flow
#         version: '1'
#         with:
#           port_expose: 8080
#           host: {gateway_host_in}
#           port_in: {gateway_port_in}
#           protocol: http
#         pods:
#         """
#     for pod_name, pea_to_args in pod_to_pea_and_args.items():
#         yaml += f"""
#           - name: {pod_name}
#             port_in: {pea_to_args[0][1]}
#             host: {pea_to_args[0][2]['host_in']}
#             external: True
#             """
#         needs = pea_to_args[0][2]['needs']
#         if needs:
#             yaml += f"""
#             needs: [{', '.join(needs)}]
#             """
#
#     # return yaml
#     base_64_yaml = base64.b64encode(yaml.encode()).decode('utf8')
#     return base_64_yaml
