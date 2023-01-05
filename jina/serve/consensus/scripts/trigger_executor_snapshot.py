import sys

import grpc
from jina.proto import jina_pb2, jina_pb2_grpc

if __name__ == '__main__':
    target = sys.argv[1]
    with grpc.insecure_channel(target) as channel:
        stub = jina_pb2_grpc.JinaExecutorSnapshotStub(channel)
        response = stub.snapshot(jina_pb2.google_dot_protobuf_dot_empty__pb2.Empty())
        print(f'Received response: {response}')
