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


class ServerWrapper:
    _DEFAULT_GRPC_OPTION = {
        'grpc.max_send_message_length': -1,
        'grpc.max_receive_message_length': -1,
        # for the following see this blog post for the choice of default value https://cs.mcgill.ca/~mxia3/2019/02/23/Using-gRPC-in-Production/
        'grpc.keepalive_time_ms': 10000,
        # send keepalive ping every 10 second, default is 2 hours.
        'grpc.keepalive_timeout_ms': 5000,
        # keepalive ping time out after 5 seconds, default is 20 seconds
        'grpc.keepalive_permit_without_calls': True,
        # allow keepalive pings when there's no gRPC calls
        'grpc.http2.max_pings_without_data': 0,
        # allow unlimited amount of keepalive pings without data
        'grpc.http2.min_time_between_pings_ms': 10000,
        # allow grpc pings from client every 10 seconds
        'grpc.http2.min_ping_interval_without_data_ms': 5000,
        # allow grpc pings from client without data every 5 seconds
    }

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self.is_cancel = asyncio.Event()
        self.host = 'localhost'
        self.port = 12345
        self.health_servicer = health.aio.HealthServicer()

        def _cancel(sig):
            def _inner_cancel(*args, **kwargs):
                print(f' received signal {sig}')
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
        print(f' running')
        self.run_forever()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f' exit')
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
        print(f' stream received')
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


# for _ in range(100):
#     p = multiprocessing.Process(target=_run_server, args=())
#     p.start()
#     from grpc_health.v1 import health_pb2, health_pb2_grpc
#
#     ready = False
#     time.sleep(1)
#     while not ready:
#         with grpc.insecure_channel(
#                 'localhost:12345',
#         ) as channel:
#             health_check_req = health_pb2.HealthCheckRequest()
#             health_check_req.service = ''
#             stub = health_pb2_grpc.HealthStub(channel)
#             resp = stub.Check(health_check_req, timeout=100)
#             print(resp)
#             ready = resp.status == health_pb2.HealthCheckResponse.ServingStatus.SERVING
#     # send requests unary_unary
#     asyncio.run(client())
#     p.terminate()
#     p.join()


from jina import Flow

for i in range(10):
    with Flow(port=12345) as f:
        print(f' HAHAHAH')
        asyncio.run(client())
        pass
        # f.post(on='/', inputs=DocumentArray.empty(100), request_size=1, stream=(i % 2 == 0))