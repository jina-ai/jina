from .base import Flow
from ..clients.mixin import AsyncPostMixin


class AsyncFlow(AsyncPostMixin, Flow):
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
        from jina.types.document.generators import from_ndarray
        import numpy as np

        with AsyncFlow().add() as f:
            await f.index(from_ndarray(np.random.random([5, 4])), on_done=print)

    Notice that the above code will NOT work in standard Python REPL, as only Jupyter/ipython implements "autoawait".

    .. seealso::
        Asynchronous in REPL: Autoawait

        https://ipython.readthedocs.io/en/stable/interactive/autoawait.html

    Another example is when using Jina as an integration. Say you have another IO-bounded job ``heavylifting()``, you
    can use this feature to schedule Jina ``index()`` and ``heavylifting()`` concurrently.

    One can think of :class:`Flow` as Jina-managed eventloop, whereas :class:`AsyncFlow` is self-managed eventloop.
    """
