import pytest

from jina.peapods.pods.factory import PodFactory
from jina.parsers import set_pod_parser

from jina import Flow, Executor, requests, Document, DocumentArray
from jina.helper import random_port
from jina.excepts import FlowTopologyError
from tests import validate_callback


def validate_response(resp):
    assert len(resp.data.docs) == 50
    for doc in resp.data.docs:
        assert 'external_real' in doc.tags['name']


@pytest.fixture(scope='function')
def input_docs():
    return DocumentArray([Document() for _ in range(50)])


@pytest.fixture
def num_replicas(request):
    return request.param


@pytest.fixture
def num_parallel(request):
    return request.param


@pytest.fixture(scope='function')
def external_pod_args(num_replicas, num_parallel):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port-in',
        str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--parallel',
        str(num_parallel),
        '--replicas',
        str(num_replicas),
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod(external_pod_args):
    return PodFactory.build_pod(external_pod_args)


class MyExternalExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests
    def foo(self, docs, *args, **kwargs):
        for doc in docs:
            doc.tags['name'] = self.runtime_args.name


@pytest.mark.parametrize('num_replicas', [1, 2], indirect=True)
@pytest.mark.parametrize('num_parallel', [1, 2], indirect=True)
def test_flow_with_external_pod(
    external_pod, external_pod_args, input_docs, mocker, num_replicas, num_parallel
):
    with external_pod:
        external_args = vars(external_pod_args)
        del external_args['name']
        del external_args['external']
        del external_args['pod_role']
        flow = Flow().add(
            **external_args,
            name='external_fake',
            external=True,
        )
        mock = mocker.Mock()
        with flow:
            flow.index(inputs=input_docs, on_done=mock)

    validate_callback(mock, validate_response)


@pytest.mark.parametrize('num_replicas', [2], indirect=True)
@pytest.mark.parametrize('num_parallel', [2], indirect=True)
def test_two_flow_with_shared_external_pod(
    external_pod, external_pod_args, input_docs, mocker, num_replicas, num_parallel
):
    with external_pod:
        external_args = vars(external_pod_args)
        del external_args['name']
        del external_args['external']
        del external_args['pod_role']
        flow = Flow().add(
            **external_args,
            name='external_fake',
            external=True,
        )

        with flow:
            results = flow.index(inputs=input_docs, return_results=True)
            validate_response(results[0])

        flow = (
            Flow()
            .add(name='foo')
            .add(
                **external_args,
                name='external_fake',
                external=True,
                needs=['gateway', 'foo'],
            )
        )

        with flow:
            flow.index(inputs=input_docs, return_results=True)
            validate_response(results[0])


@pytest.fixture(scope='function')
def external_pod_parallel_1_args(num_replicas, num_parallel):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real_1',
        '--port-in',
        str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--parallel',
        str(num_parallel),
        '--replicas',
        str(num_replicas),
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod_parallel_1(external_pod_parallel_1_args):
    return PodFactory.build_pod(external_pod_parallel_1_args)


@pytest.fixture(scope='function')
def external_pod_parallel_2_args(num_replicas, num_parallel):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real_2',
        '--port-in',
        str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--parallel',
        str(num_parallel),
        '--replicas',
        str(num_replicas),
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod_parallel_2(external_pod_parallel_2_args):
    return PodFactory.build_pod(external_pod_parallel_2_args)


@pytest.mark.parametrize('num_replicas', [1, 2], indirect=True)
@pytest.mark.parametrize('num_parallel', [1, 2], indirect=True)
def test_flow_with_external_pod_parallel(
    external_pod_parallel_1,
    external_pod_parallel_2,
    external_pod_parallel_1_args,
    external_pod_parallel_2_args,
    input_docs,
    mocker,
    num_replicas,
    num_parallel,
):

    with external_pod_parallel_1, external_pod_parallel_2:
        external_args_1 = vars(external_pod_parallel_1_args)
        external_args_2 = vars(external_pod_parallel_2_args)
        del external_args_1['name']
        del external_args_1['external']
        del external_args_1['pod_role']
        del external_args_2['name']
        del external_args_2['external']
        del external_args_2['pod_role']

        flow = (
            Flow()
            .add(name='pod1')
            .add(
                **external_args_1,
                name='external_fake_1',
                external=True,
                needs=['pod1'],
            )
            .add(
                **external_args_2,
                name='external_fake_2',
                external=True,
                needs=['pod1'],
            )
            .join(needs=['external_fake_1', 'external_fake_2'], port_in=random_port())
        )

        mock = mocker.Mock()
        with flow:
            flow.index(inputs=input_docs, on_done=mock)

    validate_callback(mock, validate_response)


@pytest.fixture(scope='function')
def external_pod_pre_parallel_args(num_replicas, num_parallel):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port-in',
        str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--parallel',
        str(num_parallel),
        '--replicas',
        str(num_replicas),
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod_pre_parallel(external_pod_pre_parallel_args):
    return PodFactory.build_pod(external_pod_pre_parallel_args)


@pytest.mark.parametrize('num_replicas', [1, 2], indirect=True)
@pytest.mark.parametrize('num_parallel', [1, 2], indirect=True)
def test_flow_with_external_pod_pre_parallel(
    external_pod_pre_parallel,
    external_pod_pre_parallel_args,
    input_docs,
    mocker,
    num_replicas,
    num_parallel,
):

    with external_pod_pre_parallel:
        external_args = vars(external_pod_pre_parallel_args)
        del external_args['name']
        del external_args['external']
        del external_args['pod_role']
        flow = (
            Flow()
            .add(
                **external_args,
                name='external_fake',
                external=True,
            )
            .add(
                name='pod1',
                needs=['external_fake'],
            )
            .add(
                name='pod2',
                needs=['external_fake'],
            )
            .join(needs=['pod1', 'pod2'])
        )
        mock = mocker.Mock()
        with flow:
            flow.index(inputs=input_docs, on_done=mock)

    validate_callback(mock, validate_response)


@pytest.fixture(scope='function')
def external_pod_join_args(num_replicas, num_parallel):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port-in',
        str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--pod-role',
        'JOIN',
        '--parallel',
        str(num_parallel),
        '--replicas',
        str(num_replicas),
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod_join(external_pod_join_args):
    return PodFactory.build_pod(external_pod_join_args)


@pytest.mark.parametrize('num_replicas', [1, 2], indirect=True)
@pytest.mark.parametrize('num_parallel', [1, 2], indirect=True)
def test_flow_with_external_pod_join(
    external_pod_join,
    external_pod_join_args,
    input_docs,
    mocker,
    num_replicas,
    num_parallel,
):
    with external_pod_join:
        external_args = vars(external_pod_join_args)
        del external_args['name']
        del external_args['external']
        del external_args['pod_role']
        flow = (
            Flow()
            .add(
                **external_args,
                external=True,
            )
            .add(
                name='pod1',
                needs=['pod0'],
            )
            .add(
                name='pod2',
                needs=['pod0'],
            )
            .join(
                **external_args,
                external=True,
                needs=['pod1', 'pod2'],
            )
        )
        mock = mocker.Mock()
        with flow:
            flow.index(inputs=input_docs, on_done=mock)

    validate_callback(mock, validate_response)
