from jina.kubernetes.naive.eap_index_flow import K8sEAPIndexFlow, PostgresConfig
from kubernetes import client, config


config.load_kube_config()
k8s_client = client.ApiClient()

NAMESPACE = 'flow4'

postgres_config = PostgresConfig(
    hostname='postgres.postgres.svc.cluster.local',
    username='postgresadmin',
    database='postgresdb',
    password='1235813'
)

K8sEAPIndexFlow(k8s_client, postgres_config, NAMESPACE).deploy()
