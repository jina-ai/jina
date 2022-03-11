import grpc

from jina.proto import jina_pb2_grpc
from jina.types.request.control import ControlRequest


def check_health_pod(addr: str, timeout: int = 600):
    """check if a pods is healthy

    :param addr: the address on which the pod is serving ex : localhost:1234
    :param timeout: timeout for the health check
    """

    channel = grpc.insecure_channel(addr)
    stub = jina_pb2_grpc.JinaControlRequestRPCStub(channel)
    request = ControlRequest(command='STATUS')
    try:
        stub.process_control(request, timeout=timeout)
    except grpc.RpcError as e:
        print('The pod is unhealthy')
        print(e)
        raise e

    print('The pod is healthy')


if __name__ == '__main__':
    """
    Health check cli (for docker):

    Example:
        python jina.resources.health_check.pod localhost:1234
    """
    import sys

    if len(sys.argv) < 2:
        raise ValueError('You need to specify a address to check health')

    addr = sys.argv[1]
    timeout = sys.argv[2] if len(sys.argv) > 2 else 600

    check_health_pod(addr, timeout)
