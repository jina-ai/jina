from typing import Callable, TYPE_CHECKING, Generator, Optional, overload

if TYPE_CHECKING:
    from ....helper import T
    from ...document import Document
    from ...arrays.document import DocumentArray


class ParallelMixin:
    """Helper functions that provide parallel map to :class:`DocumentArray` or :class:`DocumentArrayMemmap`."""

    @overload
    def apply(
        self: 'T',
        func: Callable[['Document'], 'Document'],
        backend: str = 'process',
        num_worker: Optional[int] = None,
    ) -> 'T':
        """Return a new :class:`DocumentArray` or :class:`DocumentArrayMemmap` where each element is applied with ``func``.

        :param func: a function that takes :class:`Document` as input and outputs :class:`Document`.
        :param backend: if to use multi-`process` or multi-`thread` as the parallelization backend. In general, if your
            ``func`` is IO-bound then perhaps `thread` is good enough. If your ``func`` is CPU-bound then you may use `process`.
            In practice, you should try yourselves to figure out the best value. However, if you wish to modify the elements
            in-place, regardless of IO/CPU-bound, you should always use `thread` backend.

            .. warning::
                When using `process` backend, you should not expect ``func`` modify elements in-place. This is because
                the multiprocessing backing pass the variable via pickle and work in another process. The passed object
                and the original object do **not** share the same memory.

        :param num_worker: the number of parallel workers. If not given, then the number of CPUs in the system will be used.

        """
        ...

    def apply(self: 'T', *args, **kwargs) -> 'T':
        """
        # noqa: DAR102
        # noqa: DAR101
        # noqa: DAR201
        :return: a new :class:`DocumentArray` or :class:`DocumentArrayMemmap`
        """
        new_da = type(self)()
        new_da.extend(self.map(*args, **kwargs))
        return new_da

    def map(
        self,
        func: Callable[['Document'], 'T'],
        backend: str = 'process',
        num_worker: Optional[int] = None,
    ) -> Generator['T', None, None]:
        """Return an iterator that applies function to every **element** of iterable in parallel, yielding the results.

        .. seealso::
            - To process on a batch of elements, please use :meth:`.map_batch`;
            - To return a :class:`DocumentArray`/:class:`DocumentArrayMemmap`, please use :meth:`.apply`.

        :param func: a function that takes :class:`Document` as input and outputs anything. You can either modify elements
            in-place (only with `thread` backend) or work later on return elements.
        :param backend: if to use multi-`process` or multi-`thread` as the parallelization backend. In general, if your
            ``func`` is IO-bound then perhaps `thread` is good enough. If your ``func`` is CPU-bound then you may use `process`.
            In practice, you should try yourselves to figure out the best value. However, if you wish to modify the elements
            in-place, regardless of IO/CPU-bound, you should always use `thread` backend.

            .. warning::
                When using `process` backend, you should not expect ``func`` modify elements in-place. This is because
                the multiprocessing backing pass the variable via pickle and work in another process. The passed object
                and the original object do **not** share the same memory.

        :param num_worker: the number of parallel workers. If not given, then the number of CPUs in the system will be used.
        :yield: anything return from ``func``
        """
        with _get_pool(backend, num_worker) as p:
            for x in p.imap(func, self):
                yield x

    @overload
    def apply_batch(
        self: 'T',
        func: Callable[['Document'], 'Document'],
        batch_size: int,
        backend: str = 'process',
        num_worker: Optional[int] = None,
        shuffle: bool = False,
    ) -> 'T':
        """Return a new :class:`DocumentArray` or :class:`DocumentArrayMemmap` where each element is applied with ``func``.

        :param func: a function that takes :class:`Document` as input and outputs :class:`Document`.
        :param backend: if to use multi-`process` or multi-`thread` as the parallelization backend. In general, if your
            ``func`` is IO-bound then perhaps `thread` is good enough. If your ``func`` is CPU-bound then you may use `process`.
            In practice, you should try yourselves to figure out the best value. However, if you wish to modify the elements
            in-place, regardless of IO/CPU-bound, you should always use `thread` backend.

            .. warning::
                When using `process` backend, you should not expect ``func`` modify elements in-place. This is because
                the multiprocessing backing pass the variable via pickle and work in another process. The passed object
                and the original object do **not** share the same memory.

        :param num_worker: the number of parallel workers. If not given, then the number of CPUs in the system will be used.
        :param batch_size: Size of each generated batch (except the last one, which might be smaller, default: 32)
        :param shuffle: If set, shuffle the Documents before dividing into minibatches.
        """
        ...

    def apply_batch(self: 'T', *args, **kwargs) -> 'T':
        """
        # noqa: DAR102
        # noqa: DAR101
        # noqa: DAR201
        :return: a new :class:`DocumentArray` or :class:`DocumentArrayMemmap`
        """
        new_da = type(self)()
        for _b in self.map_batch(*args, **kwargs):
            new_da.extend(_b)
        return new_da

    def map_batch(
        self,
        func: Callable[['DocumentArray'], 'T'],
        batch_size: int,
        backend: str = 'process',
        num_worker: Optional[int] = None,
        shuffle: bool = False,
    ):
        """Return an iterator that applies function to every **minibatch** of iterable in parallel, yielding the results.
        Each element in the returned iterator is :class:`DocumentArray`.

        .. seealso::
            - To process single element, please use :meth:`.map`;
            - To return :class:`DocumentArray` or :class:`DocumentArrayMemmap`, please use :meth:`.apply_batch`.

        :param batch_size: Size of each generated batch (except the last one, which might be smaller, default: 32)
        :param shuffle: If set, shuffle the Documents before dividing into minibatches.
        :param func: a function that takes :class:`DocumentArray` as input and outputs anything. You can either modify elements
            in-place (only with `thread` backend) or work later on return elements.
        :param backend: if to use multi-`process` or multi-`thread` as the parallelization backend. In general, if your
            ``func`` is IO-bound then perhaps `thread` is good enough. If your ``func`` is CPU-bound then you may use `process`.
            In practice, you should try yourselves to figure out the best value. However, if you wish to modify the elements
            in-place, regardless of IO/CPU-bound, you should always use `thread` backend.

            .. warning::
                When using `process` backend, you should not expect ``func`` modify elements in-place. This is because
                the multiprocessing backing pass the variable via pickle and work in another process. The passed object
                and the original object do **not** share the same memory.

        :param num_worker: the number of parallel workers. If not given, then the number of CPUs in the system will be used.
        :yield: anything return from ``func``
        """
        with _get_pool(backend, num_worker) as p:
            for x in p.imap(func, self.batch(batch_size=batch_size, shuffle=shuffle)):
                yield x


def _get_pool(backend, num_worker):
    if backend == 'thread':
        from multiprocessing.pool import ThreadPool as Pool

        return Pool(processes=num_worker)
    elif backend == 'process':
        from multiprocessing.pool import Pool

        return Pool(processes=num_worker)
    else:
        raise ValueError(
            f'`backend` must be either `process` or `thread`, receiving {backend}'
        )
