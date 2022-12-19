# from jina import Flow
# from jina import DocumentArray
# import asyncio
#
# for i in range(10):
#     with Flow() as f:
#         print(f' HAHAHAH')
#         pass
#         # f.post(on='/', inputs=DocumentArray.empty(100), request_size=1, stream=(i % 2 == 0))

import multiprocessing
import asyncio
import signal
import grpc
import time

from jina.proto import jina_pb2, jina_pb2_grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

_DEFAULT_GRPC_OPTIONS = [
    ('grpc.max_send_message_length', -1),
    ('grpc.max_receive_message_length', -1),
    # for the following see this blog post for the choice of default value https://cs.mcgill.ca/~mxia3/2019/02/23/Using-gRPC-in-Production/
    ('grpc.keepalive_time_ms', 10000),
    # send keepalive ping every 10 second, default is 2 hours.
    ('grpc.keepalive_timeout_ms', 5000),
    # keepalive ping time out after 5 seconds, default is 20 seconds
    ('grpc.keepalive_permit_without_calls', True),
    # allow keepalive pings when there's no gRPC calls
    ('grpc.http2.max_pings_without_data', 0),
    # allow unlimited amount of keepalive pings without data
    ('grpc.http2.min_time_between_pings_ms', 10000),
    # allow grpc pings from client every 10 seconds
    ('grpc.http2.min_ping_interval_without_data_ms', 5000),
    # allow grpc pings from client without data every 5 seconds
]


class ServerWrapper:

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self.is_cancel = asyncio.Event()
        self.host = 'localhost'
        self.port = 12345
        self.health_servicer = health.aio.HealthServicer()

        def _cancel(sig):
            def _inner_cancel(*args, **kwargs):
                self.is_cancel.set(),

            return _inner_cancel

        for sig in HANDLED_SIGNALS:
            self._loop.add_signal_handler(sig, _cancel(sig), sig, None)

        self._loop.run_until_complete(self.async_setup())

    async def async_setup(self):
        self.server = grpc.aio.server()

        jina_pb2_grpc.add_JinaRPCServicer_to_server(
            self, self.server
        )

        jina_pb2_grpc.add_JinaSingleDataRequestRPCServicer_to_server(
            self, self.server
        )

        service_names = (
            jina_pb2.DESCRIPTOR.services_by_name['JinaRPC'].full_name,
            jina_pb2.DESCRIPTOR.services_by_name['JinaSingleDataRequestRPC'].full_name,
        )
        # Mark all services as healthy.
        health_pb2_grpc.add_HealthServicer_to_server(self.health_servicer, self.server)
        bind_addr = f'{self.host}:{self.port}'
        self.server.add_insecure_port(bind_addr)
        await self.server.start()
        for service in service_names:
            await self.health_servicer.set(
                service, health_pb2.HealthCheckResponse.SERVING
            )

    def __enter__(self):
        self.run_forever()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run_forever(self):
        self._loop.run_until_complete(self._loop_body())

    async def async_run_forever(self):
        await self.server.wait_for_termination()

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPod`"""
        # threads are not using asyncio.Event, but threading.Event
        await self.is_cancel.wait()
        await self.server.stop(0)
        await self.health_servicer.enter_graceful_shutdown()

    async def _loop_body(self):
        try:
            await asyncio.gather(self.async_run_forever(), self._wait_for_cancel())
        except asyncio.CancelledError:
            print('Cancelled')

    async def Call(self, request_iterator, context=None, *args, **kwargs):
        async for resp in request_iterator:
            await asyncio.sleep(0.01)
            yield resp

    async def process_single_data(
            self, request, context=None
    ):
        print(f' single data received')
        await asyncio.sleep(0.01)
        return request


def _run_server():
    with ServerWrapper():
        pass


from jina.types.request.data import DataRequest

request = DataRequest()


async def client():
    for _ in range(50):
        async with grpc.aio.insecure_channel('localhost:12345') as channel:
            stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
            ret = await stub.process_single_data(
                request,
            )
            print(f' return {ret}')


from jina import Flow, DocumentArray, Client


async def concurrent_clients():
    async def _client(stub):
        req = DataRequest()
        return await stub.process_single_data(
            req,
        )

    async with grpc.aio.insecure_channel('localhost:12345') as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        coros = [_client(stub) for _ in range(200)]
        res = await asyncio.gather(*coros)
        print(f' res {res}')


class _Counter:
    count = 0


async def concurrent_clients_prefetch():
    PREFETCH = 50
    async with grpc.aio.insecure_channel('localhost:12345', options=_DEFAULT_GRPC_OPTIONS) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)

        def _send_future(request):
            print(f'send future {request}!!!')
            return asyncio.ensure_future(stub.process_single_data(request))

        requests_to_handle = _Counter()
        future_queue = asyncio.Queue()
        result_queue = asyncio.Queue()
        all_requests_handled = asyncio.Event()
        end_of_iter = asyncio.Event()

        async def _iterate_and_send():
            def _response_callback(resp_future):
                print(f'response done!!!')
                result_queue.put_nowait(resp_future)

            for i in range(30000):
                await asyncio.sleep(0)
                while requests_to_handle.count >= PREFETCH:
                    print(f' wait since prefetch hit')
                    await asyncio.sleep(0)
                req = DataRequest()
                requests_to_handle.count += 1
                future_response = _send_future(req)
                future_queue.put_nowait(future_response)
                future_response.add_done_callback(_response_callback)
            end_of_iter.set()

        async def receive_responses():
            while not all_requests_handled.is_set():
                future = await result_queue.get()
                response = future.result()
                print(f' response')
                yield response
                requests_to_handle.count -= 1
                if requests_to_handle.count == 0 and end_of_iter.is_set():
                    all_requests_handled.set()

        _ = asyncio.create_task(_iterate_and_send())

        result = []
        resp_i = 0
        async for resp in receive_responses():
            print(f' resp {resp_i} => {resp}')
            resp_i += 1
            result.append(resp)

        return result


# for i in range(10):
#     with Flow(port=12345) as f:
#         print(f' HAHAHAH')
#         #f.post(on='/', inputs=DocumentArray.empty(50), request_size=1, stream=False)
#         asyncio.run(parallel_clients())

for _ in range(10):
    p = multiprocessing.Process(target=_run_server, args=())
    p.start()
    from grpc_health.v1 import health_pb2, health_pb2_grpc

    ready = False
    time.sleep(1)
    while not ready:
        with grpc.insecure_channel(
                'localhost:12345',
        ) as channel:
            health_check_req = health_pb2.HealthCheckRequest()
            health_check_req.service = ''
            stub = health_pb2_grpc.HealthStub(channel)
            resp = stub.Check(health_check_req, timeout=100)
            print(resp)
            ready = resp.status == health_pb2.HealthCheckResponse.ServingStatus.SERVING
    # send requests unary_unary
    #results = asyncio.run(concurrent_clients_prefetch())
    #print(f' len {len(results)}')
    client = Client(port=12345)
    docs = client.post(on='/', inputs=DocumentArray.empty(500), request_size=1, stream=False)
    #print(f' len {len(docs)}')
    p.terminate()
    p.join()
