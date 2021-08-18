from jina import Flow

namespace = 'search-flow'
search_flow = Flow(name='search-flow', protocol='http', port_expose=8080, infrastructure='k8s').add(
    name='image_data',
    shards=3,
    replicas=2,
    polling='all',
    uses='jinahub+docker://AnnoySearcher',
    # uses='gcr.io/mystical-sweep-320315/annoy-with-grpc',
    uses_with={'dump_path': '/shared'},
    uses_after='gcr.io/jina-showcase/match-merger',
    k8s_uses_init='gcr.io/jina-showcase/postgres-dumper',
    k8s_uses_with_init={'table_name': 'image_data'},
)
search_flow.plot('search-flow.jpg')
search_flow.start()
