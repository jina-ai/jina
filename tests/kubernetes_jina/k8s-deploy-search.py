from jina import Flow
from jina.enums import InfrastructureType

namespace = 'search-flow'
search_flow = Flow(name='search-flow', protocol='http', port_expose=8080, infrastructure=InfrastructureType.K8S).add(
    name='image_data',
    shards=3,
    replicas=2,
    polling='all',
    uses='jinahub+docker://AnnoySearcher',
    # uses='gcr.io/mystical-sweep-320315/annoy-with-grpc',
    uses_with={'dump_path': '/shared'},
    uses_after='gcr.io/jina-showcase/match-merger',

    k8s_uses_with_init={'table_name': 'image_data'},
    k8s_uses_init='gcr.io/jina-showcase/postgres-dumper',
)
search_flow.plot('search-flow.jpg')
search_flow.start()
