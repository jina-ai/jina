from jina.hubble.helper import parse_hub_uri
from jina.hubble.hubio import HubIO

IS_LOCAL = False

if IS_LOCAL:
    gateway_image = 'custom-jina'
else:
    gateway_image = 'gcr.io/jina-showcase/custom-jina:latest'


def to_dns_name(name):
    return name.replace('/', '-').replace('_', '-').lower()


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
        replicas,
        pull_policy,
        init_container=None,
):
    from jina.peapods.pods.kubernetes import kubernetes_tools

    # small hack - we can always assume the ports are the same for all executors since they run on different k8s pods
    port_expose = 8080
    port_in = 8081
    port_out = 8082
    port_ctrl = 8083

    logger.info(
        f'🔋\tCreate Service for "{name}" with image "{name}" pulling from "{image_name}" \ncontainer_cmd: {container_cmd}\n{name} container_args: {container_args}'
    )
    kubernetes_tools.create(
        'service',
        {
            'name': name,
            'target': name,
            'namespace': namespace,
            'port_expose': port_expose,
            'port_in': port_in,
            'port_out': port_out,
            'port_ctrl': port_ctrl,
            'type': 'ClusterIP',
        },
    )

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
                'port_expose': port_expose,
                'port_in': port_in,
                'port_out': port_out,
                'port_ctrl': port_ctrl,
                'pull_policy': pull_policy,
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
                'port_expose': port_expose,
                'port_in': port_in,
                'port_out': port_out,
                'port_ctrl': port_ctrl,
                'pull_policy': pull_policy,
            },
        )
    return f'{name}.{namespace}.svc.cluster.local'


def get_cli_params(arguments, skip_list=()):
    arguments.host = '0.0.0.0'
    skip_attributes = [
                          'uses',  # set manually
                          'uses_with',  # set manually
                          'runtime_cls',  # set manually
                          'workspace',
                          'log_config',
                          'dynamic_routing',
                          'hosts_in_connect',
                          'polling_type',
                          'k8s_namespace',
                          'uses_after',
                          'uses_before',
                          'replicas',
                          'shards',
                          'parallel',
                          'polling',
                          'port_in',
                          'port_out',
                          'port_ctrl',
                          'port_expose',
                          'k8s_init_container_command',
                          'k8s_uses_init',
                          'k8s_mount_path',
                      ] + list(skip_list)
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

    cli_args.append('"--port-expose", "8080"')
    cli_args.append('"--port-in", "8081"')
    cli_args.append('"--port-out", "8082"')
    cli_args.append('"--port-ctrl", "8083"')

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
    return flow.build(copy_flow=True)


def dictionary_to_cli_param(dictionary):
    return dictionary.__str__().replace("'", "\\\"") if dictionary else ""


def get_needs(flow, pod):
    needs = []
    for pod_name in pod.needs:
        needed_pod = flow._pod_nodes[pod_name]
        if pod_name != 'gateway' and needed_pod.args.parallel > 1:
            needs.append(pod_name + '_tail')
        else:
            needs.append(pod_name)


def convert_to_table_name(pod_name):
    return pod_name.replace('-', '_')


def get_init_container_args(pod):
    if pod.args.k8s_uses_init:
        init_container = {
            'init-name': 'init',
            'init-image': pod.args.k8s_uses_init,
            'mount-path': pod.args.k8s_mount_path,
            'init-command': f'{pod.args.k8s_container_init_command}',
        }
    else:
        init_container = None
    return init_container
