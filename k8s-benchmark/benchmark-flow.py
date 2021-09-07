from jina import Flow
from jina.enums import InfrastructureType

f = Flow(
    name='flow',
    port_expose=8080,
    infrastructure=InfrastructureType.K8S,
    k8s_connection_pool=True,
    static_routing_table=True,
).add(
    name='executor1',
    replicas=2,
    k8s_custom_resource_dir='template',
    uses='gcr.io/jina-showcase/dummy-executor',
)

f.start()
