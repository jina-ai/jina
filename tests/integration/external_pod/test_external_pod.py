import pytest

from jina.peapods.pods import Pod, PodRoleType
from jina.parsers import set_pod_parser

from jina import Flow, Executor, requests, Document, DocumentArray
from tests import validate_callback


@pytest.fixture(scope='function')
def input_docs():
    return DocumentArray([Document() for _ in range(50)])


@pytest.fixture(scope='function')
def external_pod_args():
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port-in',
        '5000',
        '--host-in',
        '0.0.0.0',
        '--port-out',
        '3000',
        '--host-out',
        '0.0.0.0',
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod(external_pod_args):
    return Pod(
        external_pod_args,
    )


class MyExternalExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests
    def foo(self, docs, *args, **kwargs):
        for doc in docs:
            doc.tags['name'] = self.runtime_args.name


def test_flow_with_external_pod(external_pod, external_pod_args, input_docs, mocker):
    def validate_response(resp):
        assert len(resp.data.docs) == 50
        for doc in resp.data.docs:
            assert doc.tags['name'] == 'external_real'

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


@pytest.fixture(scope='function')
def external_pod_parallel_1_args():
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real_1',
        '--socket-in',
        'SUB_CONNECT',
        '--port-in',
        '3500',
        '--host-in',
        '0.0.0.0',
        '--port-out',
        '3000',
        '--host-out',
        '0.0.0.0',
        '--socket-out',
        'PUSH_CONNECT',
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod_parallel_1(external_pod_parallel_1_args):
    return Pod(
        external_pod_parallel_1_args,
    )


@pytest.fixture(scope='function')
def external_pod_parallel_2_args():
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real_2',
        '--socket-in',
        'SUB_CONNECT',
        '--port-in',
        '3500',
        '--host-in',
        '0.0.0.0',
        '--port-out',
        '3000',
        '--host-out',
        '0.0.0.0',
        '--socket-out',
        'PUSH_CONNECT',
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def external_pod_parallel_2(external_pod_parallel_2_args):
    return Pod(
        external_pod_parallel_2_args,
    )


def test_flow_with_external_pod_parallel(
    external_pod_parallel_1,
    external_pod_parallel_2,
    external_pod_parallel_1_args,
    external_pod_parallel_2_args,
    input_docs,
    mocker,
):
    def validate_response(resp):
        assert len(resp.data.docs) == 50
        for doc in resp.data.docs:
            assert doc.tags['name'] in {'external_real_1', 'external_real_2'}

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
            .add(name='pod1', port_out=3500)
            .add(
                **external_args_1, name='external_fake_1', external=True, needs=['pod1']
            )
            .add(
                **external_args_2, name='external_fake_2', external=True, needs=['pod1']
            )
            .join(needs=['external_fake_1', 'external_fake_2'], port_in=3000)
        )

        mock = mocker.Mock()
        with flow:
            flow.index(inputs=input_docs, on_done=mock)

    validate_callback(mock, validate_response)
