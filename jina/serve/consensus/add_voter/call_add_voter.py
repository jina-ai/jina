import grpc
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
            add_voter_result = stub.Await(future)
            _ = stub.Forget(future)
            if not add_voter_result.error:
                return True
            else:
                return False
        except:
            return False


async def async_call_add_voter(target, replica_id, voter_address):
    async with grpc.aio.insecure_channel(target) as channel:
        stub = RaftAdminStub(channel)

        req = AddVoterRequest(
            id=replica_id,
            address=voter_address,
            previous_index=0,
        )

        try:
            future = await stub.AddVoter(req)
            add_voter_result = await stub.Await(future)
            _ = await stub.Forget(future)
            if not add_voter_result.error:
                return True
            else:
                return False
        except:
            return False
