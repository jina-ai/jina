from functools import partialmethod
from typing import Dict, Optional

from ...clients.base import InputType, CallbackFnType


class CRUDFlowMixin:
    """The synchronous version of the Mixin for CRUD in Flow"""

    def post(
            self,
            on: str,
            inputs: InputType,
            on_done: CallbackFnType = None,
            on_error: CallbackFnType = None,
            on_always: CallbackFnType = None,
            parameters: Optional[Dict] = None,
            target_peapod: Optional[str] = None,
            **kwargs,
    ):
        """Post a general data request to the Flow.

        :param inputs: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_peapod: a regex string represent the certain peas/pods request targeted
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        :return: results
        """
        return self._get_client(**kwargs).post(
            on,
            inputs,
            on_done,
            on_error,
            on_always,
            parameters,
            target_peapod,
            **kwargs,
        )

    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')
