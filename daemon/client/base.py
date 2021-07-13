from typing import Dict, Optional, Union

import requests

from jina.logging.logger import JinaLogger
from jina.importer import ImportExtensions

from ..models import DaemonID
from .helper import jinad_alive, daemonize, error_msg_from


class BaseClient:
    """
    JinaD baseclient.

    :param host: the host address of ``jinad`` instance
    :param port: the port number of ``jinad`` instance
    :param timeout: stop waiting for a response after a given number of seconds with the timeout parameter.
    """

    kind = ''
    endpoint = '/'

    def __init__(
        self,
        uri: str,
        logger: JinaLogger,
        timeout: int = None,
    ):
        self.logger = logger
        self.timeout = timeout
        self.http_uri = f'http://{uri}'
        self.store_api = f'{self.http_uri}{self.endpoint}'
        self.logstream_api = f'ws://{uri}/logstream'

    @jinad_alive
    def alive(self) -> bool:
        """
        Return True if `jinad` is alive at remote

        :return: True if `jinad` is alive at remote else false
        """
        r = requests.get(url=self.http_uri, timeout=self.timeout)
        return r.status_code == requests.codes.ok

    @jinad_alive
    def status(self) -> Optional[Dict]:
        """
        Get status of remote `jinad`

        :return: dict status of remote jinad
        """
        r = requests.get(url=f'{self.http_uri}/status', timeout=self.timeout)
        if r.status_code == requests.codes.ok:
            return r.json()

    @jinad_alive
    def get(self, identity: Union[str, DaemonID]) -> Optional[Union[str, Dict]]:
        """Get status of the remote object

        :param id: identity of the Pea/Pod
        :raises: requests.exceptions.RequestException
        :return: json response of the remote Pea / Pod status
        """

        r = requests.get(
            url=f'{self.store_api}/{daemonize(identity, self.kind)}',
            timeout=self.timeout,
        )
        response_json = r.json()
        if r.status_code == requests.codes.unprocessable:
            self.logger.error(
                f'validation error in the request: {error_msg_from(response_json)}'
            )
            return response_json['body']
        elif r.status_code == requests.codes.not_found:
            self.logger.error(
                f'couldn\'t find {identity} in remote {self.kind.title()} store'
            )
            return response_json['detail']
        else:
            self.logger.success(f'Found {self.kind.title()} {identity} in store')
            return response_json

    @jinad_alive
    def list(self) -> Dict:
        """
        List all objects in the store

        :return: json response of the remote Pea / Pod status
        """
        r = requests.get(url=self.store_api, timeout=self.timeout)
        response_json = r.json()
        self.logger.success(
            f'Found {len(response_json.get("items", []))} {self.kind.title()} in store'
        )
        return response_json['items'] if 'items' in response_json else response_json

    def create(self, *args, **kwargs) -> Dict:
        """
        Create an object in the store

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    def delete(self, identity: DaemonID, *args, **kwargs) -> str:
        """
        Delete an object in the store

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def logstream(self, id: str):
        """Websocket log stream from remote Pea / Pod

        :param id:  the identity of that Pea / Pod
        """
        with ImportExtensions(required=True):
            import websockets

        remote_log_config = os.path.join(__resources_path__, 'logging.remote.yml')
        all_remote_loggers = {}
        try:
            url = f'{self.logstream_api}/{id}'
            async with websockets.connect(url) as websocket:
                async for log_line in websocket:
                    try:
                        ll = json.loads(log_line)
                        name = ll['name']
                        if name not in all_remote_loggers:
                            all_remote_loggers[name] = JinaLogger(
                                context=ll['host'], log_config=remote_log_config
                            )

                        all_remote_loggers[name].info(
                            '{host} {name} {type} {message}'.format_map(ll)
                        )
                    except json.decoder.JSONDecodeError:
                        continue
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.warning(f'log streaming is disconnected')
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(
                f'log streaming is disabled, you won\'t see logs on the remote\n Reason: {e!r}'
            )
        except asyncio.CancelledError:
            self.logger.warning(f'log streaming is cancelled')
        finally:
            for l in all_remote_loggers.values():
                l.close()
