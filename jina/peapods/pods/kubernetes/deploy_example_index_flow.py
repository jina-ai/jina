from jina.kubernetes.naive.otto_index_flow import K8sOttoIndexFlow, PostgresConfig
from kubernetes import client, config


config.load_kube_config()
k8s_client = client.ApiClient()

postgres_config = PostgresConfig(
    hostname='postgres.postgres.svc.cluster.local',
    username='postgresadmin',
    database='postgresdb',
    password='1235813',
)

K8sOttoIndexFlow(k8s_client, postgres_config).deploy()
