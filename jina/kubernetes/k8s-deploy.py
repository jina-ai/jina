from jina import Flow

dump_path = '/shared'

service_name = 'cliptext7'
namespace = 'search-flow'
search_flow = (
    Flow(
        name='search-flow',
        protocol='http',
        port_expose=8080,
        # host='gateway.search-flow.svc.cluster.local'
    # ).add(
    #     name='cliptext7',
    #     uses='jinahub+docker://CLIPTextEncoder',
    #     # uses='jinahub+docker://Sentencizer',
    #     # uses='docker://jinaai/jina',
    #     # peas_hosts=  [ # don't - it overwrites host and tries to use JinaD
    #     #     f'{service_name}-head.{namespace}.svc.cluster.local',
    #     #     f'{service_name}-tail.{namespace}.svc.cluster.local',
    #     #     f'{service_name}-pea-{0}.{namespace}.svc.cluster.local',
    #     #     f'{service_name}-pea-{1}.{namespace}.svc.cluster.local',
    #     # ],
    #     shards=2,
    #     polling='all',
    # )
    # .add(
    #     name='cliptext2',
    #     uses='jinahub+docker://CLIPTextEncoder',
    #     needs='gateway',
    #     shards=1,
    #     polling='any',
    # )
    ).add(
        name='searcher1',
        shards=2,
        polling='all',
        uses='jinahub+docker://AnnoySearcher',
        uses_with={'dump_path': dump_path},
        uses_after='gcr.io/jina-showcase/match-merger',
        # needs=['cliptext'],
    )
    # .add(
    #     name='searcher2',
    #     shards=2,
    #     polling='all',
    #     uses='jinahub+docker://AnnoySearcher',
    #     uses_with={'dump_path': dump_path},
    #     uses_after='gcr.io/jina-showcase/match-merger',
    #     needs=['cliptext2'],
    # )
    # .add(
    #     name='ranker',
    #     uses='jinahub+docker://MinRanker',
    #     uses_with={'metric': 'cosine'},
    #     needs=['searcher1', 'searcher2'],
    # )
)

# print('deploy index flow')
# index_flow.plot('jina/kubernetes/index_flow.jpg')
# index_flow.deploy_naive('k8s')


# with search_flow:
#     search_flow.block()


print('deploy search flow')
# search_flow.plot('jina/kubernetes/search_flow.jpg')
search_flow.deploy_naive('k8s')
print('done')
