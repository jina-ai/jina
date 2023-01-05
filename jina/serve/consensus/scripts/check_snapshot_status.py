import sys

import grpc
from jina.proto import jina_pb2, jina_pb2_grpc

if __name__ == '__main__':
    target = sys.argv[1]
    id = sys.argv[2]
    with grpc.insecure_channel(target) as channel:
        stub = jina_pb2_grpc.JinaExecutorSnapshotProgressStub(channel)
        response = stub.snapshot_status(jina_pb2.SnapshotId(value=id))
        print(f'Received response: {response}')
