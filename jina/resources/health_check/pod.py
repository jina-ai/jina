def check_health_pod(addr: str):
    """check if a pods is healthy

    :param addr: the address on which the pod is serving ex : localhost:1234
    """
    import grpc

    from jina.serve.networking import GrpcConnectionPool
    from jina.types.request.control import ControlRequest

    try:
        GrpcConnectionPool.send_request_sync(
            request=ControlRequest('STATUS'),
            target=addr,
        )
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
    check_health_pod(addr)
