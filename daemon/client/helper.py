from typing import Dict
import requests

from ..models import DaemonID


def daemonize(identity: str, kind: str = 'workspace') -> DaemonID:
    try:
        return DaemonID(identity)
    except TypeError:
        return DaemonID(f'j{kind}-{identity}')


def jinad_alive(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except requests.exceptions.RequestException as ex:
            self.logger.error(
                f'couldn\'t connect to jinad! please check if it is alive: {ex!r}'
            )

    return wrapper


def error_msg_from(response: Dict) -> str:
    assert 'detail' in response, '\'detail\' not found in response'
    assert 'body' in response, '\'body\' not found in response'
    return response['body']
    # return '\n'.join(j for j in response['body'])
