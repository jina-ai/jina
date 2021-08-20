import os
from typing import Optional

from kubernetes import utils
from kubernetes.utils import FailToCreateError

from jina.peapods.pods.kubernetes import kubernetes_tools

from jina.peapods.pods.kubernetes import PostgresConfig
from jina.logging.logger import JinaLogger


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
        )
