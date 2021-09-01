from jina import Flow
from jina.enums import InfrastructureType

f = Flow(name='flow', port_expose=8080, infrastructure=InfrastructureType.K8S).add(
    name='executor1',
    replicas=2,
)

f.start()
