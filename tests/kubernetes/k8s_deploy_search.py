from jina import Flow

namespace = 'search-flow'
shards = 2
search_flow = Flow(
    name=namespace, protocol='http', port_expose=8080, infrastructure='k8s'
).add(
    name='image_data',
    shards=shards,
    replicas=2,
    polling='all',
    # uses='jinahub+docker://AnnoySearcher',
    # uses='gcr.io/mystical-sweep-320315/annoy-with-grpc',
    uses_with={'dump_path': '/shared'},
    uses_after='gcr.io/jina-showcase/match-merger',
    k8s_uses_with_init={
        'table_name': 'image_data',
        'postgres_svc': 'postgres.postgres.svc.cluster.local',
        'shards': shards,
        'dump_path': '/shared',
    },
    k8s_uses_init='gcr.io/jina-showcase/postgres-dumper',
)
# search_flow.plot('search-flow.jpg')
search_flow.start()
