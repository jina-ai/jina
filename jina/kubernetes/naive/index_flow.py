import base64
import os
from dataclasses import dataclass
from typing import Optional, Dict

from kubernetes.utils import FailToCreateError
from jina.hubble.hubio import HubIO
from jina.kubernetes.naive.naive_deployment import to_dns_name
from jina.peapods.pods import Pod

from jina import Flow
from jina.hubble.helper import parse_hub_uri
from jina.kubernetes import kubernetes_tools
from jina.logging.logger import JinaLogger
from kubernetes import utils


@dataclass
class PostgresConfig:
    hostname: str
    username: str
    database: str


class PostgresDefaultDeployment:

    RESOURCES = {
        'config': 'postgres-configmap.yml',
        'deployment': 'postgres-deployment.yml',
        'pv': 'postgres-pv.yml',
        'pvc': 'postgres-pvc.yml',
        'service': 'postgres-service.yml',
    }

    def __init__(
        self,
        k8s_client,
        path_to_config_folder: Optional[str] = 'jina/kubernetes/postgres_deployment',
    ):
        self._k8s_client = k8s_client
        self._path_to_config_folder = path_to_config_folder
        self._logger = JinaLogger(self.__class__.__name__)

    def deploy(self) -> PostgresConfig:
        kubernetes_tools.create('namespace', {'name': 'postgres'})
        for name, yaml_file in PostgresDefaultDeployment.RESOURCES.items():
            path_to_yml = os.path.join(self._path_to_config_folder, yaml_file)
            try:
                utils.create_from_yaml(self._k8s_client, path_to_yml)
                self._logger.info(f'Created resource {name} from yml file {yaml_file}')
            except FailToCreateError as e:
                if e.api_exceptions[0].status == 409:
                    self._logger.info(f'Resource {name} exists already.')
                else:
                    raise e
        service_dns = 'postgres.postgres.svc.cluster.local'
        return PostgresConfig(
            hostname=service_dns,
            username='postgresadmin',
            database='postgresdb',
            password='1235813',
        )


class JinaPodAsMicroService:
    """ Deploys a single executor as a micro-service-styled deployment + service in kubernetes. """

    def __init__(self, jina_pod: Pod, namespace: str, service_port: int = 8081):
        self._pod = jina_pod
        self._logger = JinaLogger(self.__class__.__name__)
        self._namespace = namespace
        self._service_port = service_port

    def deploy_as_micro_service(self):
        pod_to_args = {}
        scheme, name, tag, secret = parse_hub_uri(self._pod.args.uses)
        meta_data = HubIO.fetch_meta(name)
        image_name = meta_data.image_name
        replicas = self._pod.args.replicas
        override_with = self._pod.args.override_with

        self._logger.info(
            f'🔋\tCreate Service for "{self._pod.name}" with image "{name}" pulling from "{image_name}"'
        )
        self._create_service(name)
        pod_to_args[self._pod.name] = {
            'host_in': f'{to_dns_name(name)}.{self._namespace}.svc.cluster.local'
        }

        self._logger.info(
            f'🐳\tCreate Deployment for "{image_name}" with replicas {replicas}'
        )
        self._create_deployment(image_name, name, replicas, override_with)
        return pod_to_args

    def _create_deployment(self, image_name, name, replicas, override_with):
        container_args = (
            "[\"--uses\", \"config.yml\", "
            "\"--port-in\", \"8081\","
            " \"--dynamic-routing-in\","
            " \"--dynamic-routing-out\","
            " \"--socket-in\", \"ROUTER_BIND\","
            " \"--socket-out\", \"ROUTER_BIND\"]"
        )
        if override_with is not None:
            override_with = override_with.__str__().replace("'", "\"")
            container_args = (
                f"[\"--override-with\", \'{override_with}\', " + container_args[1:]
            )

        kubernetes_tools.create(
            'deployment',
            {
                'name': name.lower(),
                'namespace': self._namespace,
                'image': image_name,
                'replicas': replicas,
                'command': "",
                'args': container_args,
                'port': self._service_port,
            },
        )

    def _create_service(self, name):
        kubernetes_tools.create(
            'service',
            {
                'name': name.lower(),
                'target': name.lower(),
                'namespace': self._namespace,
                'port': self._service_port,
                'type': 'ClusterIP',
            },
        )


class K8sIndexFlow:

    GENERIC_GATEWAY_CONTAINER_NAME = 'gcr.io/mystical-sweep-320315/generic-gateway'

    def __init__(self, k8s_client, postgres_config: Optional[PostgresConfig] = None):
        self._postgres_config = postgres_config
        self._k8s = k8s_client
        self._logger = JinaLogger(self.__class__.__name__)
        self._namespace = 'f1'

    @property
    def flow_object(self) -> Flow:
        return (
            Flow()
            .add(name='cliptext', uses='jinahub+docker://CLIPTextEncoder')
            .add(
                name='storage',
                uses='jinahub+docker://PostgreSQLStorage',
                override_with=self._postgres_config.__dict__,
            )
        )

    def deploy(self):
        kubernetes_tools.create('namespace', {'name': self._namespace})
        if self._postgres_config is None:
            self._postgres_config = self._deploy_postgres()
        pods_configs = self._deploy_pods()
        self._deploy_gateway(pod_to_args=pods_configs)
        self._deploy_ingress()

    def _deploy_gateway(self, pod_to_args: Dict):
        self._logger.info(f'🔒\tCreate "gateway service"')

        def _create_gateway_service(namespace: str, name: str, port: int) -> None:
            kubernetes_tools.create(
                'service',
                {
                    'name': name,
                    'target': 'gateway',
                    'namespace': namespace,
                    'port': port,
                    'type': 'ClusterIP',
                },
            )

        _create_gateway_service(self._namespace, 'gateway-exposed', 8080)
        _create_gateway_service(self._namespace, 'gateway-in', 8081)

        gateway_yaml = self._create_gateway_yaml(
            pod_to_args, 'gateway-in.f1.svc.cluster.local'
        )
        kubernetes_tools.create(
            'deployment',
            {
                'name': 'gateway',
                'replicas': 1,
                'port': 8080,
                'command': "[\"python\"]",
                'args': f"[\"gateway.py\", \"{gateway_yaml}\"]",
                'image': self.GENERIC_GATEWAY_CONTAINER_NAME,
                'namespace': self._namespace,
            },
        )

    def _deploy_pods(self) -> Dict:
        pods_to_args = {}
        for pod_name, pod in self.flow_object._pod_nodes.items():
            if pod_name == 'gateway':
                continue
            pod_to_args = JinaPodAsMicroService(
                pod, self._namespace
            ).deploy_as_micro_service()
            pods_to_args.update(pod_to_args)
        return pods_to_args

    def _deploy_postgres(self) -> PostgresConfig:
        postgres_default_deployment = PostgresDefaultDeployment(self._k8s)
        return postgres_default_deployment.deploy()

    @staticmethod
    def _create_gateway_yaml(pod_to_args, gateway_host_in):
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
        for pod, args in pod_to_args.items():
            yaml += f"""
          - name: {pod}
            port_in: 8081
            host: {args['host_in']}
            external: True
            """

        # return yaml
        base_64_yaml = base64.b64encode(yaml.encode()).decode('utf8')
        return base_64_yaml

    def _deploy_ingress(self):
        kubernetes_tools.create_gateway_ingress(self._namespace)
