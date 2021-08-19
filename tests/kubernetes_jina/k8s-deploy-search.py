from jina import Flow
from jina.enums import InfrastructureType

namespace = 'search-flow'
shards=3
search_flow = Flow(name=namespace, protocol='http', port_expose=8080, infrastructure=InfrastructureType.K8S).add(
    name='image_data',
    shards=shards,
    replicas=2,
    polling='all',
    uses='jinahub+docker://AnnoySearcher',
    # uses='gcr.io/mystical-sweep-320315/annoy-with-grpc',
    uses_with={'dump_path': '/shared'},
    uses_after='gcr.io/jina-showcase/match-merger',
)
search_flow.plot('search-flow.jpg')
search_flow.start()
