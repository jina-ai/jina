from typing import Union, Sequence

from ...clients.base import CallbackFnType


class AsyncControlFlowMixin:
    """The asynchronous version of the Mixin for controlling, scaling the Flow"""

    async def reload(
        self,
        targets: Union[str, Sequence[str]],
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs,
    ):
        """Reload the executor of certain peas/pods in the Flow
        It will start a :py:class:`CLIClient` and call :py:func:`reload`.

        :param targets: the regex string or list of regex strings to match the pea/pod names.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        :yield: result
        """
        async for r in self._get_client(**kwargs).reload(
            targets, on_done, on_error, on_always, **kwargs
        ):
            yield r
