import grpc
import time
from jina.serve.consensus.add_voter.add_voter_pb2_grpc import RaftAdminStub
from jina.serve.consensus.add_voter.add_voter_pb2 import AddVoterRequest


def call_add_voter(target, replica_id, voter_address):
    with grpc.insecure_channel(target) as channel:
        stub = RaftAdminStub(channel)

        req = AddVoterRequest(
            id=replica_id,
            address=voter_address,
            previous_index=0,
        )

        try:
            future = stub.AddVoter(req)
            time.sleep(2)
            _ = stub.Await(future)
            stub.Forget(future)
            return True
        except grpc.RpcError:
            return False
