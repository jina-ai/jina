__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import request
from .base import BaseClient, CallbackFnType, InputFnType
from .helper import callback_exec
from .request import GeneratorSourceType
from ..enums import RequestType
from ..helper import run_async, deprecated_alias


class Client(BaseClient):
    """A simple Python client for connecting to the gateway.
    It manges the asyncio eventloop internally, so all interfaces are synchronous from the outside.
    """

    @deprecated_alias(buffer='input_fn', callback='on_done', output_fn='on_done')
    def train(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
              **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.TRAIN
        run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    @deprecated_alias(buffer='input_fn', callback='on_done', output_fn='on_done')
    def search(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
               **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.SEARCH
        run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    @deprecated_alias(buffer='input_fn', callback='on_done', output_fn='on_done')
    def index(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
              **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.INDEX
        run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)
