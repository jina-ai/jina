import time
import uuid
from collections.abc import MutableMapping
from contextlib import contextmanager
from typing import Dict, Any

from jina.helper import colored
from .. import daemon_logger
from ..helper import delete_meta_files_from_upload


class BaseStore(MutableMapping):

    def __init__(self):
        self._items = {}  # type: Dict['uuid.UUID', Dict[str, Any]]
        self._time_last_update = time.perf_counter()
        self._logger = daemon_logger
        self._credentials = 'foo:bar'
        self._session_token = None

    @contextmanager
    def session(self):
        # TODO(Deepankar): Implement fastapi based oauth/bearer security here
        # https://github.com/jina-ai/jinad/issues/4

        if self._session_token:
            yield
            return

        self._session_token = self.login(self._credentials)
        try:
            yield
        finally:
            self.logout(self._session_token)

    def login(self, creds):
        # TODO: implement login-logout here to manage session token
        token = hash(creds)
        self._logger.debug(f'LOGIN: {token}')
        return token

    def logout(self, token):
        self._logger.debug(f'LOGOUT: {token}')

    def add(self, *args, **kwargs) -> 'uuid.UUID':
        """Add a new element to the store. This method needs to be overridden by the subclass"""
        raise NotImplementedError

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key: 'uuid.UUID'):
        return self._items[key]

    def __delitem__(self, key: 'uuid.UUID'):
        """ Release a Pea/Pod/Flow object from the store """
        if key not in self._items:
            raise KeyError(f'{key} not found in store.')

        v = self._items[key]
        v['object'].close()
        for current_file in v.get('files', []):
            delete_meta_files_from_upload(current_file=current_file)
        v.pop('object')
        v.pop('files')

        t = time.perf_counter()
        v['time_terminate'] = t
        self._time_last_update = t
        self._logger.success(f'{key} is released')

    def __setitem__(self, key: 'uuid.UUID', value: Dict) -> None:
        self._items[key] = value
        t = time.perf_counter()
        value.update({'time_start': t})
        self._time_last_update = t
        self._logger.success(f'add {value!r} with id {colored(str(key), "cyan")} to the store')
