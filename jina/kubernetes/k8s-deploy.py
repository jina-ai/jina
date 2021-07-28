from jina import Flow
from tests.integration.v2_api.test_docs_matrix_tail_pea import MatchMerger

f = (
    Flow(name='f1')
    .add(name='cliptext', uses='jinahub+docker://CLIPTextEncoder', replicas=2)
    .add(name='cliptext2', uses='jinahub+docker://CLIPTextEncoder', needs='gateway', replicas=3)
    .add(name='textindexer', shards=2, uses='jinahub+docker://SimpleIndexer', uses_after=MatchMerger, needs=['cliptext'])
    .add(name='textindexer2', uses='jinahub+docker://SimpleIndexer', needs=['cliptext2'])
    .add(name='ranker', uses='jinahub+docker://LightGBMRanker', needs=['textindexer', 'textindexer2'])
)
f.plot('jina/kubernetes/flow.jpg')
f.deploy_naive('k8s')
print('done')