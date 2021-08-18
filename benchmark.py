import time
from enum import Enum

import click

from jina import Flow, Document, DocumentArray
from jina.excepts import RuntimeFailToStart

PORT_EXPOSE = 12345
SHARD_COUNT = 25
FLOW_LENGTH = 25
REQUEST_CONTENT_LENGTH = 10000

# TODO: remote, reconnect hack, serialize hack, dont send routing table hack
# problem: large routing tables, serializing same message multiple times, main difference is between shards and need, not between zmq and grpc
# bug port assignment


def long_flow(mode, always_reconnect, shard_count):
    flow = Flow(
        port_expose=PORT_EXPOSE,
        grpc_data_requests=True if mode == 'grpc' else False,
        always_reconnect=always_reconnect,
    )
    for i in range(FLOW_LENGTH):
        flow = flow.add(name=f'exec_{i}', uses='dummy_exec.yml')
    return flow


def sharded_flow(mode, always_reconnect, shard_count):
    return Flow(
        port_expose=PORT_EXPOSE,
        grpc_data_requests=True if mode == 'grpc' else False,
        always_reconnect=always_reconnect,
    ).add(name=f'exec', uses='dummy_exec.yml', shards=shard_count, polling='ALL')


def needs_flow(mode, always_reconnect, shard_count):
    flow = Flow(
        port_expose=PORT_EXPOSE,
        grpc_data_requests=True if mode == 'grpc' else False,
        always_reconnect=always_reconnect,
    )
    for i in range(shard_count):
        flow = flow.add(name=f'exec_{i}', uses='dummy_exec.yml', needs='gateway')
    flow = flow.needs_all()
    return flow


def init_flow(flow_creator, mode, always_reconnect, shard_count):
    flow = flow_creator(mode, always_reconnect, shard_count)
    flow.start()
    for i in range(100):
        flow.index(DocumentArray([Document(content=f'{i}' * REQUEST_CONTENT_LENGTH)]))
    return flow


def run_benchmark(mode, flow_type, request_count, shard_count, always_reconnect=False):
    while True:
        try:
            flow = init_flow(flow_type, mode, always_reconnect, shard_count)
            break
        except RuntimeFailToStart:
            pass

    content = 's' * REQUEST_CONTENT_LENGTH
    da = DocumentArray([Document(content=content)])

    start_time = time.time()
    for i in range(request_count):
        result = flow.search(da)
    end_time = time.time()

    flow.close()
    time.sleep(1.0)

    return end_time - start_time


def run_benchmarks(request_count, shard_count):

    print('run grpc benchmark wide')
    grpc_benchmark_time_wide = run_benchmark(
        'grpc', needs_flow, request_count, shard_count
    )

    print('run zmq benchmark wide/needs')
    zmq_benchmark_time_needs = run_benchmark(
        'zmq', needs_flow, request_count, shard_count
    )
    print('run zmq benchmark wide/shards')
    zmq_benchmark_time_shards = run_benchmark(
        'zmq', sharded_flow, request_count, shard_count
    )

    print(f'requests {request_count}')
    print(f'SHARD_COUNT {shard_count}')
    print(f'FLOW_LENGTH {FLOW_LENGTH}')
    print(f'REQUEST_CONTENT_LENGTH {REQUEST_CONTENT_LENGTH}')

    print('grpc')

    print(
        f'wide: total: {grpc_benchmark_time_wide} s, per request: {1000*(grpc_benchmark_time_wide/request_count)} ms, per hop: {1000*(grpc_benchmark_time_wide/request_count)/shard_count} ms'
    )

    print('zmq')

    print(
        f'wide (needs): total: {zmq_benchmark_time_needs} s, per request: {1000*(zmq_benchmark_time_needs/request_count)} ms, per hop: {1000*(zmq_benchmark_time_needs/request_count)/shard_count} ms'
    )
    print(
        f'wide (shards): total: {zmq_benchmark_time_shards} s, per request: {1000*(zmq_benchmark_time_shards/request_count)} ms, per hop: {1000*(zmq_benchmark_time_shards/request_count)/shard_count} ms'
    )

    # print('zmq - reconnect')
    # print(f'long: {zmq_benchmark_time_long_reconnect}')
    # print(f'wide (needs): {zmq_benchmark_time_needs_reconnect}')
    # print(f'wide (shards): {zmq_benchmark_time_shards_reconnect}')


def run_long_benchmarks(request_count, shard_count):
    print('run zmq benchmark long - reconnect')
    zmq_benchmark_time_long_reconnect = run_benchmark(
        'zmq', long_flow, request_count, shard_count, always_reconnect=True
    )
    # print('run zmq benchmark wide/needs - reconnect')
    # zmq_benchmark_time_needs_reconnect = run_benchmark(
    #     'zmq', needs_flow, request_count, always_reconnect=True
    # )
    # print('run zmq benchmark wide/shards - reconnect')
    # zmq_benchmark_time_shards_reconnect = run_benchmark(
    #     'zmq', sharded_flow, request_count, always_reconnect=True
    # )
    print('run grpc benchmark long')
    grpc_benchmark_time_long = run_benchmark(
        'grpc', long_flow, request_count, shard_count
    )
    print('run zmq benchmark long')
    zmq_benchmark_time_long = run_benchmark(
        'zmq', long_flow, request_count, shard_count
    )

    print(f'requests {request_count}')
    print(f'FLOW_LENGTH {FLOW_LENGTH}')

    print(
        f'grpc long: total: {grpc_benchmark_time_long} s, per request: {1000 * (grpc_benchmark_time_long / request_count)} ms, per hop: {1000 * (grpc_benchmark_time_long / request_count) / FLOW_LENGTH} ms'
    )
    print(
        f'zmq long: total: {zmq_benchmark_time_long} s, per request: {1000 * (zmq_benchmark_time_long / request_count)} ms, per hop: {1000 * (zmq_benchmark_time_long / request_count) / FLOW_LENGTH} ms'
    )


# default=['grpc', 'zmq', 'zmq_reconnect'],
@click.command()
@click.option(
    '--requests', default=100, help='Number of search requests to use for benchmarking'
)
def start(requests):
    shards = 1
    run_long_benchmarks(requests, None)
    while shards < 65:
        print(f'run with {shards} shards')
        run_benchmarks(request_count=requests, shard_count=shards)
        shards += shards


if __name__ == '__main__':
    start()
