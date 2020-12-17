__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import request
from .base import BaseClient, CallbackFnType, InputFnType
from .helper import callback_exec
from .request import GeneratorSourceType
from ..enums import RequestType
from ..helper import run_async


class Client(BaseClient):
    """A simple Python client for connecting to the gateway.
    It manges the asyncio eventloop internally, so all interfaces are synchronous from the outside.
    """

    def train(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
              **kwargs) -> None:
        self.mode = RequestType.TRAIN
        run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    def search(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
               **kwargs) -> None:
        self.mode = RequestType.SEARCH
        run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    def index(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
              **kwargs) -> None:
        self.mode = RequestType.INDEX
        run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)
