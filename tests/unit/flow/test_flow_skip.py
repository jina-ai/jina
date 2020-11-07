from jina.enums import OnErrorSkip
from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from jina.proto import jina_pb2


class DummyCrafter(BaseCrafter):
    def craft(self, *args, **kwargs):
        return 1 / 0


def test_bad_flow_skip_handle():
    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code >= jina_pb2.Status.ERROR]
        assert len(bad_routes) == 3
        assert req.status.code == jina_pb2.Status.ERROR
        assert bad_routes[0].pod == 'r1'
        assert bad_routes[1].pod == 'r2'
        assert bad_routes[1].status.code == jina_pb2.Status.ERROR_CHAINED
        assert bad_routes[2].pod == 'r3'
        assert bad_routes[2].status.code == jina_pb2.Status.ERROR_CHAINED

    f = (Flow(skip_on_error=OnErrorSkip.HANDLE).add(name='r1', uses='DummyCrafter')
         .add(name='r2')
         .add(name='r3'))

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)


def test_bad_flow_skip_exec():
    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code >= jina_pb2.Status.ERROR]
        assert len(bad_routes) == 1
        assert req.status.code == jina_pb2.Status.ERROR
        assert bad_routes[0].pod == 'r1'

    f = (Flow(skip_on_error=OnErrorSkip.EXECUTOR).add(name='r1', uses='DummyCrafter')
         .add(name='r2')
         .add(name='r3'))

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
