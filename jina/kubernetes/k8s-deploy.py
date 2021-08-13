from jina import Flow


namespace = 'search-flow'
search_flow = Flow(name='search-flow', protocol='http', port_expose=8080).add(
    name='image_data',
    shards=3,
    replicas=2,
    polling='all',
    # uses='jinahub+docker://AnnoySearcher',
    uses='gcr.io/mystical-sweep-320315/annoy-with-grpc',
    uses_with={'dump_path': '/shared'},
    uses_after='gcr.io/jina-showcase/match-merger',
)
search_flow.plot('search-flow.jpg')
search_flow.deploy('k8s')
