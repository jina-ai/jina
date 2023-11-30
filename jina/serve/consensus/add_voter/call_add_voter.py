import grpc
import time
from jina.serve.consensus.add_voter.add_voter_pb2_grpc import RaftAdminStub
from jina.serve.consensus.add_voter.add_voter_pb2 import AddVoterRequest


def call_add_voter(target, replica_id, voter_address, logger):
    logger.error(f'JOAN HERE HEY LEADER {target} add {voter_address} for ID {replica_id}')
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
                logger.error(f'SUCCESFULLY ADDED VOTER {voter_address} to leader {target} for ID {replica_id}')
                return True
            else:
                return False
        except Exception as e:
            logger.error(f'2-Exception {e}')
            return False