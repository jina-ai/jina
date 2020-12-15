from typing import Union, List, Iterator, Callable
from urllib.request import Request

from . import Flow
from ..clients import InputFnType
from ..clients.asyncio import AsyncClient

if False:
    import numpy as np


class AsyncFlow(Flow):
    """
    :class:`AsyncFlow` is the asynchronous version of the :class:`Flow`. They share the same interface, except
    in :class:`AsyncFlow` :meth:`train`, :meth:`index`, :meth:`search` methods are coroutines
    (i.e. declared with the async/await syntax), simply calling them will not schedule them to be executed.
    To actually run a coroutine, user need to put them in an eventloop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncFlow` can be very useful in
    the integration settings, where Jina/Jina flow is NOT the main logic, but rather served as a part of other program.
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
            await f.index_ndarray(np.random.random([5, 4]), output_fn=print)

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
                await f.index_ndarray(np.random.random([5, 4]), output_fn=validate)


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

    async def train(self, input_fn: InputFnType = None,
                    output_fn: Callable[['Request'], None] = None,
                    **kwargs):
        """Do training on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`train`.

        Example,

        .. highlight:: python
        .. code-block:: python

            with f:
                f.train(input_fn)
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'   # each yield generates a document for training

            with f.build(runtime='thread') as flow:
                flow.train(bytes_gen=my_reader())

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param output_fn: the callback function to invoke after training
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        await self._get_client(**kwargs).train(input_fn, output_fn, **kwargs)

    async def index_ndarray(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
                            output_fn: Callable[['Request'], None] = None,
                            **kwargs):
        """Using numpy ndarray as the index source for the current flow

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the the numpy data source beforehand
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import input_numpy
        await self._get_client(**kwargs).index(input_numpy(array, axis, size, shuffle),
                                               output_fn, **kwargs)

    async def search_ndarray(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
                             output_fn: Callable[['Request'], None] = None,
                             **kwargs):
        """Use a numpy ndarray as the query source for searching on the current flow

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the the numpy data source beforehand
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import input_numpy
        await self._get_client(**kwargs).search(input_numpy(array, axis, size, shuffle),
                                                output_fn, **kwargs)

    async def index_lines(self, lines: Iterator[str] = None, filepath: str = None, size: int = None,
                          sampling_rate: float = None, read_mode='r',
                          output_fn: Callable[['Request'], None] = None,
                          **kwargs):
        """ Use a list of lines as the index source for indexing on the current flow

        :param lines: a list of strings, each is considered as d document
        :param filepath: a text file that each line contains a document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import input_lines
        await self._get_client(**kwargs).index(input_lines(lines, filepath, size, sampling_rate, read_mode),
                                               output_fn, **kwargs)

    async def index_files(self, patterns: Union[str, List[str]], recursive: bool = True,
                          size: int = None, sampling_rate: float = None, read_mode: str = None,
                          output_fn: Callable[['Request'], None] = None,
                          **kwargs):
        """ Use a set of files as the index source for indexing on the current flow

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files and
                    zero or more directories and subdirectories.
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary mode
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import input_files
        await self._get_client(**kwargs).index(input_files(patterns, recursive, size, sampling_rate, read_mode),
                                               output_fn, **kwargs)

    async def search_files(self, patterns: Union[str, List[str]], recursive: bool = True,
                           size: int = None, sampling_rate: float = None, read_mode: str = None,
                           output_fn: Callable[['Request'], None] = None,
                           **kwargs):
        """ Use a set of files as the query source for searching on the current flow

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files and
                    zero or more directories and subdirectories.
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import input_files
        await self._get_client(**kwargs).search(input_files(patterns, recursive, size, sampling_rate, read_mode),
                                                output_fn, **kwargs)

    async def search_lines(self, filepath: str = None, lines: Iterator[str] = None, size: int = None,
                           sampling_rate: float = None, read_mode='r',
                           output_fn: Callable[['Request'], None] = None,
                           **kwargs):
        """ Use a list of files as the query source for searching on the current flow

        :param filepath: a text file that each line contains a document
        :param lines: a list of strings, each is considered as d document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import input_lines
        await self._get_client(**kwargs).search(input_lines(lines, filepath, size, sampling_rate, read_mode),
                                                output_fn, **kwargs)

    async def index(self, input_fn: InputFnType = None,
                    output_fn: Callable[['Request'], None] = None,
                    **kwargs):
        """Do indexing on the current flow

        Example,

        .. highlight:: python
        .. code-block:: python

            with f:
                f.index(input_fn)
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'  # each yield generates a document to index

            with f.build(runtime='thread') as flow:
                flow.index(bytes_gen=my_reader())

        It will start a :py:class:`CLIClient` and call :py:func:`index`.

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        await self._get_client(**kwargs).index(input_fn, output_fn, **kwargs)

    async def search(self, input_fn: InputFnType = None,
                     output_fn: Callable[['Request'], None] = None,
                     **kwargs):
        """Do searching on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`search`.


        Example,

        .. highlight:: python
        .. code-block:: python

            with f:
                f.search(input_fn)
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'   # each yield generates a query for searching

            with f.build(runtime='thread') as flow:
                flow.search(bytes_gen=my_reader())

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param output_fn: the callback function to invoke after searching
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        await self._get_client(**kwargs).search(input_fn, output_fn, **kwargs)
