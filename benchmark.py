import time
from enum import Enum

import click

from jina import Flow, Document, DocumentArray

PORT_EXPOSE = 12345
SHARD_COUNT = 25
FLOW_LENGTH = 25

# TODO: remote, different request sizes, reconnect


def long_flow(mode, always_reconnect):
    flow = Flow(
        port_expose=PORT_EXPOSE, grpc_data_requests=True if mode == 'grpc' else False
    )
    for i in range(FLOW_LENGTH):
        flow = flow.add(name=f'exec_{i}', uses='dummy_exec.yml')
    return flow


def sharded_flow(mode, always_reconnect):
    return Flow(
        port_expose=PORT_EXPOSE, grpc_data_requests=True if mode == 'grpc' else False
    ).add(name=f'exec', uses='dummy_exec.yml', shards=SHARD_COUNT, polling='ALL')


def needs_flow(mode, always_reconnect):
    flow = Flow(
        port_expose=PORT_EXPOSE, grpc_data_requests=True if mode == 'grpc' else False
    )
    for i in range(SHARD_COUNT):
        flow = flow.add(name=f'exec_{i}', uses='dummy_exec.yml', needs='gateway')
    flow = flow.needs_all()
    return flow


def init_flow(flow_creator, mode, always_reconnect):
    flow = flow_creator(mode, always_reconnect)
    flow.start()
    for i in range(100):
        flow.index(DocumentArray([Document(content=f'{i}')]))
    return flow


def run_benchmark(mode, flow_type, request_count, always_reconnect=False):
    flow = init_flow(flow_type, mode, always_reconnect)

    start_time = time.time()
    for i in range(request_count):
        result = flow.search(DocumentArray([Document(content='1')]))
    end_time = time.time()

    flow.close()
    time.sleep(1.0)

    return end_time - start_time


def run_benchmarks(request_count):
    # print('run zmq benchmark long - reconnect')
    # #zmq_benchmark_time_long_reconnect = run_benchmark('zmq', long_flow, request_count, always_reconnect=True)
    # print('run zmq benchmark wide/needs - reconnect')
    # #zmq_benchmark_time_needs_reconnect = run_benchmark('zmq', needs_flow, request_count, always_reconnect=True)
    # print('run zmq benchmark wide/shards - reconnect')
    # zmq_benchmark_time_shards_reconnect = run_benchmark('zmq', sharded_flow, request_count, always_reconnect=True)

    print('run zmq benchmark long')
    zmq_benchmark_time_long = run_benchmark('zmq', long_flow, request_count)
    print('run zmq benchmark wide/needs')
    zmq_benchmark_time_needs = run_benchmark('zmq', needs_flow, request_count)
    print('run zmq benchmark wide/shards')
    zmq_benchmark_time_shards = run_benchmark('zmq', sharded_flow, request_count)

    print('run grpc benchmark long')
    grpc_benchmark_time_long = run_benchmark('grpc', long_flow, request_count)
    print('run grpc benchmark wide')
    grpc_benchmark_time_wide = run_benchmark('grpc', needs_flow, request_count)

    print(f'requests {request_count}')
    print(f'SHARD_COUNT {SHARD_COUNT}')
    print(f'FLOW_LENGTH {FLOW_LENGTH}')

    print('grpc')
    print(f'long: {grpc_benchmark_time_long}')
    print(f'wide: {grpc_benchmark_time_wide}')

    print('zmq')
    print(f'long: {zmq_benchmark_time_long}')
    print(f'wide (needs): {zmq_benchmark_time_needs}')
    print(f'wide (shards): {zmq_benchmark_time_shards}')


# default=['grpc', 'zmq', 'zmq_reconnect'],
@click.command()
@click.option(
    '--requests', default=100, help='Number of search requests to use for benchmarking'
)
def start(requests):
    run_benchmarks(request_count=requests)


if __name__ == '__main__':
    start()
