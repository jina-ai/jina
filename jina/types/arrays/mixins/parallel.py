from typing import Callable, TYPE_CHECKING, Generator, Optional

if TYPE_CHECKING:
    from ....helper import T
    from ...document import Document


class ParallelMixin:
    """Helper functions that provide parallel map to :class:`DocumentArray` or :class:`DocumentArrayMemmap`."""

    def map(
        self,
        func: Callable[['Document'], 'T'],
        backend: str = 'process',
        num_worker: Optional[int] = None,
    ) -> Generator['T', None, None]:
        """Return an iterator that applies function to every item of iterable in parallel, yielding the results.

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
        if backend == 'thread':
            from multiprocessing.pool import ThreadPool as Pool
        elif backend == 'process':
            from multiprocessing.pool import Pool
        else:
            raise ValueError(
                f'`backend` must be either `process` or `thread`, receiving {backend}'
            )
        with Pool(processes=num_worker) as p:
            for x in p.imap(func, self):
                yield x
