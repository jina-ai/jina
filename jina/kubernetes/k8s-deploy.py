from jina import Flow


index_flow = (
    Flow(name='index-flow')
    .add(name='cliptext', uses='jinahub+docker://CLIPTextEncoder', shards=2, polling='any')
    .add(name='cliptext2', uses='jinahub+docker://CLIPTextEncoder', needs='gateway', shards=3, polling='any')
    .add(name='textindexer', uses='jinahub+docker://SimpleIndexer',  needs=['cliptext'])
    .add(name='textindexer2', uses='jinahub+docker://SimpleIndexer', needs=['cliptext2'])
)

search_flow = (
    Flow(name='search-flow2')
    .add(name='cliptext', uses='jinahub+docker://CLIPTextEncoder', shards=2, polling='any')
    .add(name='cliptext2', uses='jinahub+docker://CLIPTextEncoder', needs='gateway', shards=3, polling='any')
    .add(name='searcher1', shards=2, polling='all', uses='jinahub+docker://SimpleIndexer', uses_after='gcr.io/jina-showcase/match-merger', needs=['cliptext'])
    .add(name='searcher2', shards=2, polling='all', uses='jinahub+docker://SimpleIndexer', uses_after='gcr.io/jina-showcase/match-merger', needs=['cliptext2'])
    .add(name='ranker', uses='jinahub+docker://MinRanker', override_with={'metric': 'cosine'}, needs=['searcher1', 'searcher2'])
)

# print('deploy index flow')
# index_flow.plot('jina/kubernetes/index_flow.jpg')
# index_flow.deploy_naive('k8s')

print('deploy search flow')
search_flow.plot('jina/kubernetes/search_flow.jpg')
search_flow.deploy_naive('k8s')
print('done')