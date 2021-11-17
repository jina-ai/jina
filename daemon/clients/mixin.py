from functools import partialmethod

from jina.helper import run_async


class AsyncToSyncMixin:
    """Mixin to convert `async def`s to `def`"""

    def func(self, func_name, *args, **kwargs):
        """convert async method `func_name` to a normal method

        :param func_name: name of method in super
        :param args: positional args
        :param kwargs: keyword args
        :return: run func_name from super
        """
        f = getattr(super(), func_name, None)
        if f:
            return run_async(f, any_event_loop=True, *args, **kwargs)

    alive = partialmethod(func, 'alive')
    status = partialmethod(func, 'status')
    get = partialmethod(func, 'get')
    list = partialmethod(func, 'list')
    arguments = partialmethod(func, 'arguments')
    create = partialmethod(func, 'create')
    update = partialmethod(func, 'update')
    rolling_update = partialmethod(func, 'rolling_update')
    scale = partialmethod(func, 'scale')
    delete = partialmethod(func, 'delete')
