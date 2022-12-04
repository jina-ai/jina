from jina import Executor, requests, dynamic_batching, Flow, Document, DocumentArray
from pathlib import Path

class MyExecutor(Executor):
    @requests(on=['/cat', '/kitten'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def cat_fun(self, docs, **kwargs):
        return DocumentArray([Document(text='cat')])
    
    @requests()
    @dynamic_batching(preferred_batch_size=10, timeout=10000)
    def default_fun(self, docs, **kwargs):
        return DocumentArray([Document(text='bar')])


def test_dynamic_batching_config(tmpdir):
    TMPDIR: Path = Path(tmpdir)
    f =Flow(port=12345).add(
        uses=MyExecutor,
        name='exec0',
        uses_dynamic_batching={'/foo': {'preferred_batch_size': 2, 'timeout': 4000}}
    )
    f.save_config(str(TMPDIR / 'flow0.yml'))

    f1 = Flow.load_config(str(TMPDIR / 'flow0.yml'))
    assert f._deployment_nodes['exec0'].args.uses_dynamic_batching == f1._deployment_nodes['exec0'].args.uses_dynamic_batching
