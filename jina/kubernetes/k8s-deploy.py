from jina import Flow


namespace = 'search-flow'
search_flow = Flow(name='search-flow', protocol='http', port_expose=8080).add(
    name='text_index',
    shards=2,
    polling='all',
    uses='jinahub+docker://AnnoySearcher',
    uses_with={'dump_path': '/shared'},
    uses_after='gcr.io/jina-showcase/match-merger',
)

search_flow.deploy('k8s')
