import uuid

import pytest

import jina.excepts
from jina import Document, DocumentArray, Executor, Flow, requests
from jina.helper import random_port
from jina.orchestrate.deployments import Deployment
from jina.parsers import set_deployment_parser
from jina.serve.helper import get_server_side_grpc_options


def validate_response(docs, expected_docs=50):
    assert len(docs) == expected_docs
    for doc in docs:
        assert 'external_real' in doc.tags['name']


@pytest.fixture(scope='function')
def input_docs():
    return DocumentArray([Document() for _ in range(50)])


@pytest.fixture
def num_shards(request):
    return request.param


def _external_deployment_args(num_shards, port=None):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port',
        str(port) if port else str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


@pytest.fixture(scope='function')
def external_deployment_args(num_shards, port=None):
    return _external_deployment_args(num_shards, port)


@pytest.fixture
def external_deployment(external_deployment_args):
    return Deployment(external_deployment_args)


class MyExternalExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = str(uuid.uuid4())

    @requests
    def foo(self, docs, *args, **kwargs):
        for doc in docs:
            doc.tags['name'] = self.runtime_args.name
            doc.tags['uuid'] = self._id


@pytest.mark.parametrize('num_shards', [1, 2], indirect=True)
def test_flow_with_external_deployment(
    external_deployment, external_deployment_args, input_docs, num_shards
):
    with external_deployment:
        external_args = vars(external_deployment_args)
        del external_args['name']
        del external_args['external']
        del external_args['deployment_role']
        print(external_args)
        flow = Flow().add(
            **external_args,
            name='external_fake',
            external=True,
        )
        with flow:
            resp = flow.index(inputs=input_docs)

        # expect 50 reduced Documents in total after sharding
        validate_response(resp, 50)


@pytest.mark.parametrize('num_shards', [2], indirect=True)
def test_two_flow_with_shared_external_deployment(
    external_deployment, external_deployment_args, input_docs, num_shards
):
    external_deployment.head_args.disable_reduce = True
    with external_deployment:
        external_args = vars(external_deployment_args)
        del external_args['name']
        del external_args['external']
        del external_args['deployment_role']
        flow1 = Flow().add(
            **external_args,
            name='external_fake',
            external=True,
        )

        flow2 = (
            Flow()
            .add(name='foo')
            .add(
                **external_args,
                name='external_fake',
                external=True,
                needs=['gateway', 'foo'],
            )
        )
        with flow1, flow2:
            results = flow1.index(inputs=input_docs)

            # Reducing applied after shards, expect only 50 docs
            validate_response(results, 50)

            # Reducing applied after sharding and the needs
            results = flow2.index(inputs=input_docs)
            validate_response(results, 50)


@pytest.fixture(scope='function')
def external_deployment_shards_1_args(num_shards):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real_1',
        '--port',
        str(random_port()),
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


@pytest.fixture
def external_deployment_shards_1(external_deployment_shards_1_args):
    return Deployment(external_deployment_shards_1_args)


@pytest.fixture(scope='function')
def external_deployment_shards_2_args(num_shards):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real_2',
        '--port',
        str(random_port()),
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


@pytest.fixture
def external_deployment_shards_2(external_deployment_shards_2_args):
    return Deployment(external_deployment_shards_2_args)


@pytest.mark.parametrize('num_shards', [1, 2], indirect=True)
def test_flow_with_external_deployment_shards(
    external_deployment_shards_1,
    external_deployment_shards_2,
    external_deployment_shards_1_args,
    external_deployment_shards_2_args,
    input_docs,
    num_shards,
):
    with external_deployment_shards_1, external_deployment_shards_2:
        external_args_1 = vars(external_deployment_shards_1_args)
        external_args_2 = vars(external_deployment_shards_2_args)
        del external_args_1['name']
        del external_args_1['external']
        del external_args_1['deployment_role']
        del external_args_2['name']
        del external_args_2['external']
        del external_args_2['deployment_role']
        flow = (
            Flow()
            .add(name='executor1')
            .add(
                **external_args_1,
                name='external_fake_1',
                external=True,
                needs=['executor1'],
            )
            .add(
                **external_args_2,
                name='external_fake_2',
                external=True,
                needs=['executor1'],
            )
            .needs(needs=['external_fake_1', 'external_fake_2'], port=random_port())
        )

        with flow:
            resp = flow.index(inputs=input_docs)

        # Reducing applied on shards and needs, expect 50 docs
        validate_response(resp, 50)


@pytest.fixture(scope='function')
def external_deployment_pre_shards_args(num_shards):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port',
        str(random_port()),
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


@pytest.fixture
def external_deployment_pre_shards(external_deployment_pre_shards_args):
    return Deployment(external_deployment_pre_shards_args)


@pytest.mark.parametrize('num_shards', [1, 2], indirect=True)
def test_flow_with_external_deployment_pre_shards(
    external_deployment_pre_shards,
    external_deployment_pre_shards_args,
    input_docs,
    num_shards,
):
    with external_deployment_pre_shards:
        external_args = vars(external_deployment_pre_shards_args)
        del external_args['name']
        del external_args['external']
        del external_args['deployment_role']
        flow = (
            Flow()
            .add(
                **external_args,
                name='external_fake',
                external=True,
            )
            .add(
                name='executor1',
                needs=['external_fake'],
            )
            .add(
                name='executor2',
                needs=['external_fake'],
            )
            .needs(['executor1', 'executor2'])
        )
        with flow:
            resp = flow.index(inputs=input_docs)

        # Reducing applied on shards and needs, expect 50 docs
        validate_response(resp, 50)


@pytest.fixture(scope='function')
def external_deployment_join_args(num_shards):
    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port',
        str(random_port()),
        '--deployment-role',
        'JOIN',
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


@pytest.fixture
def external_deployment_join(external_deployment_join_args):
    return Deployment(external_deployment_join_args)


@pytest.mark.parametrize('num_shards', [1, 2], indirect=True)
def test_flow_with_external_deployment_join(
    external_deployment_join,
    external_deployment_join_args,
    input_docs,
    num_shards,
):
    with external_deployment_join:
        external_args = vars(external_deployment_join_args)
        del external_args['name']
        del external_args['external']
        del external_args['deployment_role']
        flow = (
            Flow()
            .add(
                **external_args,
                external=True,
            )
            .add(
                name='executor1',
                needs=['executor0'],
            )
            .add(
                name='executor2',
                needs=['executor0'],
            )
            .needs(
                **external_args,
                external=True,
                needs=['executor1', 'executor2'],
            )
        )
        with flow:
            resp = flow.index(inputs=input_docs)

        # Reducing applied everywhere, expect 50 docs, same as the input
        validate_response(resp, len(input_docs))


def test_external_flow_with_target_executor():
    class ExtExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'external'

    external_flow = Flow().add(uses=ExtExecutor)

    with external_flow:
        d = Document(text='sunset with green landscape by the river')
        f = Flow().add(port=external_flow.port, external=True, name='external_executor')
        with f:
            response = f.post(on='/', inputs=d, target_executor='external_executor')

    assert response[0].text == 'external'


def test_external_flow_with_grpc_metadata():
    import grpc
    from grpc_health.v1 import health_pb2, health_pb2_grpc
    from grpc_reflection.v1alpha import reflection

    from jina.proto import jina_pb2, jina_pb2_grpc
    from jina.serve.runtimes.gateway.grpc import GRPCGateway

    class DummyInterceptor(grpc.aio.ServerInterceptor):
        def __init__(self):
            def deny(_, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid key')

            self._deny = grpc.unary_unary_rpc_method_handler(deny)

        async def intercept_service(self, continuation, handler_call_details):
            meta = handler_call_details.invocation_metadata
            method = handler_call_details.method
            if method != '/jina.JinaRPC/Call':
                return await continuation(handler_call_details)

            for m in meta:
                if m == ('authorization', 'valid'):
                    return await continuation(handler_call_details)

            return self._deny

    class DummyGRPCGateway(GRPCGateway):
        def __int__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def grpc_extra_server_interceptors(self):
            return [DummyInterceptor()]

        async def setup_server(self):
            """
            setup GRPC server
            """
            server_interceptors = self.grpc_tracing_server_interceptors or []
            extra_interceptors = self.grpc_extra_server_interceptors()
            if extra_interceptors:
                server_interceptors.extend(extra_interceptors)

            self.server = grpc.aio.server(
                options=get_server_side_grpc_options(self.grpc_server_options),
                interceptors=server_interceptors,
            )

            jina_pb2_grpc.add_JinaRPCServicer_to_server(
                self.streamer._streamer, self.server
            )

            jina_pb2_grpc.add_JinaGatewayDryRunRPCServicer_to_server(
                self._request_handler, self.server
            )
            jina_pb2_grpc.add_JinaInfoRPCServicer_to_server(
                self._request_handler, self.server
            )

            service_names = (
                jina_pb2.DESCRIPTOR.services_by_name['JinaRPC'].full_name,
                jina_pb2.DESCRIPTOR.services_by_name['JinaGatewayDryRunRPC'].full_name,
                jina_pb2.DESCRIPTOR.services_by_name['JinaInfoRPC'].full_name,
                reflection.SERVICE_NAME,
            )
            # Mark all services as healthy.
            health_pb2_grpc.add_HealthServicer_to_server(
                self.health_servicer, self.server
            )

            for service in service_names:
                await self.health_servicer.set(
                    service, health_pb2.HealthCheckResponse.SERVING
                )
            reflection.enable_server_reflection(service_names, self.server)

            bind_addr = f'{self.host}:{self.port}'

            if self.ssl_keyfile and self.ssl_certfile:
                with open(self.ssl_keyfile, 'rb') as f:
                    private_key = f.read()
                with open(self.ssl_certfile, 'rb') as f:
                    certificate_chain = f.read()

                server_credentials = grpc.ssl_server_credentials(
                    (
                        (
                            private_key,
                            certificate_chain,
                        ),
                    )
                )
                self.server.add_secure_port(bind_addr, server_credentials)
            elif (
                self.ssl_keyfile != self.ssl_certfile
            ):  # if we have only ssl_keyfile and not ssl_certfile or vice versa
                raise ValueError(
                    f"you can't pass a ssl_keyfile without a ssl_certfile and vice versa"
                )
            else:
                self.server.add_insecure_port(bind_addr)
            self.logger.debug(f'start server bound to {bind_addr}')
            await self.server.start()

    class ExtExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'external'

    external_flow = Flow().config_gateway(uses=DummyGRPCGateway).add(uses=ExtExecutor)

    with external_flow:
        d = Document(text='sunset with green landscape by the river')
        f = Flow().add(
            port=external_flow.port,
            external=True,
            name='external_executor',
            grpc_metadata={'authorization': 'valid'},
        )
        with f:
            response = f.post(on='/', inputs=d, target_executor='external_executor')

            assert response[0].text == 'external'

        f = Flow().add(
            port=external_flow.port,
            external=True,
            name='external_executor',
            grpc_metadata={'authorization': 'invalid'},
        )
        with f:
            with pytest.raises(jina.excepts.BadServerFlow) as error_info:
                response = f.post(on='/', inputs=d, target_executor='external_executor')
            assert 'Invalid key' in str(error_info.value)
            # assert response[0].text == 'external'
