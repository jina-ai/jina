from jina.resources.health_check.pod import check_health_pod


def check_health_http(addr):
    import requests

    try:
        resp = requests.get(f'http://{addr}/')
        if not resp.status_code == 200:
            raise RuntimeError(
                f'The http gateway is unhealthy http status : {resp.status_code}'
            )
    except requests.exceptions.RequestException as e:
        print('The http gateway is unhealthy')
        raise e

    print('The http gateway is healthy')


async def check_health_websocket(addr):
    import websockets

    try:
        async with websockets.connect(f'ws://{addr}') as websocket:
            pass
    except websockets.exceptions.WebSocketException as e:
        print('The websocket gateway is unhealthy')
        raise e

    print('The websocket gateway is healthy')


if __name__ == '__main__':
    """
    Health check cli (for docker):

    Example:
        python jina.resources.health_check.pod localhost:1234 http
    """
    import sys

    if len(sys.argv) < 3:
        raise ValueError(
            'You need to specify a address to check health and at protocol'
        )

    addr = sys.argv[1]
    protocol = sys.argv[2]

    if protocol == 'grpc':
        check_health_pod(addr)
    elif protocol == 'http':
        check_health_http(addr)
    elif protocol == 'websocket':
        import asyncio

        asyncio.run(check_health_websocket(addr))
    else:
        raise ValueError(f'{protocol} should be in ["grpc","http","websocket"]')
