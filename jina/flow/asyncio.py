from .base import BaseFlow
from .mixin.async_crud import AsyncCRUDFlowMixin
from ..clients.asyncio import AsyncClient, AsyncWebSocketClient


class AsyncFlow(AsyncCRUDFlowMixin, BaseFlow):
    """
    :class:`AsyncFlow` is the asynchronous version of the :class:`Flow`. They share the same interface, except
    in :class:`AsyncFlow` :meth:`train`, :meth:`index`, :meth:`search` methods are coroutines
    (i.e. declared with the async/await syntax), simply calling them will not schedule them to be executed.
    To actually run a coroutine, user need to put them in an eventloop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncFlow` can be very useful in
    the integration settings, where Jina/Jina Flow is NOT the main logic, but rather served as a part of other program.
    In this case, users often do not want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Flow`
    is controlling and wrapping the eventloop internally, making the Flow looks synchronous from outside.

    In particular, :class:`AsyncFlow` makes Jina usage in Jupyter Notebook more natural and reliable.
    For example, the following code
    will use the eventloop that already spawned in Jupyter/ipython to run Jina Flow (instead of creating a new one).

    .. highlight:: python
    .. code-block:: python

        from jina import AsyncFlow
        import numpy as np

        with AsyncFlow().add() as f:
            await f.index_ndarray(np.random.random([5, 4]), on_done=print)

    Notice that the above code will NOT work in standard Python REPL, as only Jupyter/ipython implements "autoawait".

    .. seealso::
        Asynchronous in REPL: Autoawait

        https://ipython.readthedocs.io/en/stable/interactive/autoawait.html

    Another example is when using Jina as an integration. Say you have another IO-bounded job ``heavylifting()``, you
    can use this feature to schedule Jina ``index()`` and ``heavylifting()`` concurrently. For example,

    .. highlight:: python
    .. code-block:: python

        async def run_async_flow_5s():
            # WaitDriver pause 5s makes total roundtrip ~5s
            with AsyncFlow().add(uses='- !WaitDriver {}') as f:
                await f.index_ndarray(np.random.random([5, 4]), on_done=validate)


        async def heavylifting():
            # total roundtrip takes ~5s
            print('heavylifting other io-bound jobs, e.g. download, upload, file io')
            await asyncio.sleep(5)
            print('heavylifting done after 5s')


        async def concurrent_main():
            # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
            await asyncio.gather(run_async_flow_5s(), heavylifting())


    One can think of :class:`Flow` as Jina-managed eventloop, whereas :class:`AsyncFlow` is self-managed eventloop.
    """
    _cls_client = AsyncClient  #: the type of the Client, can be changed to other class

    def _update_client(self):
        if self._pod_nodes['gateway'].args.restful:
            self._cls_client = AsyncWebSocketClient
