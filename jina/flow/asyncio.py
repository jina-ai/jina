import warnings
from typing import Union, Iterable, TextIO, Dict

from .base import BaseFlow
from ..clients.asyncio import AsyncClient, AsyncWebSocketClient
from ..clients.base import InputFnType, CallbackFnType
from ..enums import DataInputType
from ..helper import deprecated_alias

if False:
    import numpy as np


class AsyncFlow(BaseFlow):
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

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def train(self, input_fn: InputFnType,
                    on_done: CallbackFnType = None,
                    on_error: CallbackFnType = None,
                    on_always: CallbackFnType = None,
                    **kwargs):
        """Do training on the current flow

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        warnings.warn(f'{self.train} is under heavy refactoring', FutureWarning)
        async for r in self._get_client(**kwargs).train(input_fn, on_done, on_error, on_always, **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def index_ndarray(self,
                            array: 'np.ndarray',
                            axis: int = 0,
                            size: int = None,
                            shuffle: bool = False,
                            on_done: CallbackFnType = None,
                            on_error: CallbackFnType = None,
                            on_always: CallbackFnType = None,
                            **kwargs):
        """Using numpy ndarray as the index source for the current flow

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the the numpy data source beforehand
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_ndarray
        async for r in self._get_client(**kwargs).index(_input_ndarray(array, axis, size, shuffle),
                                                        on_done, on_error, on_always, data_type=DataInputType.CONTENT,
                                                        **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def search_ndarray(self,
                             array: 'np.ndarray',
                             axis: int = 0,
                             size: int = None,
                             shuffle: bool = False,
                             on_done: CallbackFnType = None,
                             on_error: CallbackFnType = None,
                             on_always: CallbackFnType = None,
                             **kwargs):
        """Use a numpy ndarray as the query source for searching on the current flow

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the the numpy data source beforehand
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_ndarray
        async for r in self._get_client(**kwargs).search(_input_ndarray(array, axis, size, shuffle),
                                                         on_done, on_error, on_always, data_type=DataInputType.CONTENT,
                                                         **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def index_lines(self,
                          lines: Union[Iterable[str], TextIO] = None,
                          filepath: str = None,
                          size: int = None,
                          sampling_rate: float = None,
                          read_mode: str = 'r',
                          line_format: str = 'json',
                          field_resolver: Dict[str, str] = None,
                          on_done: CallbackFnType = None,
                          on_error: CallbackFnType = None,
                          on_always: CallbackFnType = None,
                          **kwargs):
        """ Use a list of lines as the index source for indexing on the current flow

        :param lines: a list of strings, each is considered as d document
        :param filepath: a text file that each line contains a document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param line_format: the format of each line: ``json`` or ``csv``
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
            names defined in Protobuf. This is only used when the given ``document`` is
            a JSON string or a Python dict.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_lines
        async for r in self._get_client(**kwargs).index(
                _input_lines(lines, filepath,
                             size=size,
                             sampling_rate=sampling_rate,
                             read_mode=read_mode,
                             line_format=line_format,
                             field_resolver=field_resolver),
                on_done, on_error, on_always, data_type=DataInputType.AUTO,
                **kwargs):
            yield r

    async def index_csv(self,
                        lines: Union[Iterable[str], TextIO],
                        field_resolver: Dict[str, str] = None,
                        size: int = None,
                        sampling_rate: float = None,
                        on_done: CallbackFnType = None,
                        on_error: CallbackFnType = None,
                        on_always: CallbackFnType = None,
                        **kwargs):
        """ Use a list of lines as the index source for indexing on the current flow
        :param lines: a list of strings, each is considered as d document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
            names defined in Protobuf. This is only used when the given ``document`` is
            a JSON string or a Python dict.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_csv
        async for r in self._get_client(**kwargs).index(
                _input_csv(lines,
                           size=size,
                           sampling_rate=sampling_rate,
                           field_resolver=field_resolver),
                on_done, on_error, on_always, data_type=DataInputType.AUTO, **kwargs):
            yield r

    async def index_ndjson(self,
                           lines: Union[Iterable[str], TextIO],
                           field_resolver: Dict[str, str] = None,
                           size: int = None,
                           sampling_rate: float = None,
                           on_done: CallbackFnType = None,
                           on_error: CallbackFnType = None,
                           on_always: CallbackFnType = None,
                           **kwargs):
        """ Use a list of lines as the index source for indexing on the current flow
        :param lines: a list of strings, each is considered as d document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
            names defined in Protobuf. This is only used when the given ``document`` is
            a JSON string or a Python dict.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_ndjson
        async for r in self._get_client(**kwargs).index(
                _input_ndjson(lines,
                              size=size,
                              sampling_rate=sampling_rate,
                              field_resolver=field_resolver),
                on_done, on_error, on_always, data_type=DataInputType.AUTO, **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def index_files(self, patterns: Union[str, Iterable[str]], recursive: bool = True,
                          size: int = None, sampling_rate: float = None, read_mode: str = None,
                          on_done: CallbackFnType = None,
                          on_error: CallbackFnType = None,
                          on_always: CallbackFnType = None,
                          **kwargs):
        """ Use a set of files as the index source for indexing on the current flow

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files and
                    zero or more directories and subdirectories.
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary mode
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_files
        async for r in self._get_client(**kwargs).index(
                _input_files(patterns, recursive, size, sampling_rate, read_mode),
                on_done, on_error, on_always, data_type=DataInputType.CONTENT,
                **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def search_files(self,
                           patterns: Union[str, Iterable[str]],
                           recursive: bool = True,
                           size: int = None, sampling_rate: float = None, read_mode: str = None,
                           on_done: CallbackFnType = None,
                           on_error: CallbackFnType = None,
                           on_always: CallbackFnType = None,
                           **kwargs):
        """ Use a set of files as the query source for searching on the current flow

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files and
                    zero or more directories and subdirectories.
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_files
        async for r in self._get_client(**kwargs).search(
                _input_files(patterns, recursive, size, sampling_rate, read_mode),
                on_done, on_error, on_always, data_type=DataInputType.CONTENT, **kwargs):
            yield r

    async def search_ndjson(self,
                            lines: Union[Iterable[str], TextIO],
                            field_resolver: Dict[str, str] = None,
                            size: int = None,
                            sampling_rate: float = None,
                            on_done: CallbackFnType = None,
                            on_error: CallbackFnType = None,
                            on_always: CallbackFnType = None,
                            **kwargs):
        """ Use a list of files as the query source for searching on the current flow
        :param lines: a list of strings, each is considered as d document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
            names defined in Protobuf. This is only used when the given ``document`` is
            a JSON string or a Python dict.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_ndjson
        async for r in self._get_client(**kwargs).search(
                _input_ndjson(lines,
                              size=size,
                              sampling_rate=sampling_rate,
                              field_resolver=field_resolver),
                on_done, on_error, on_always, data_type=DataInputType.AUTO, **kwargs):
            yield r

    async def search_csv(self,
                         lines: Union[Iterable[str], TextIO],
                         field_resolver: Dict[str, str] = None,
                         size: int = None,
                         sampling_rate: float = None,
                         on_done: CallbackFnType = None,
                         on_error: CallbackFnType = None,
                         on_always: CallbackFnType = None,
                         **kwargs):
        """ Use a list of lines as the index source for indexing on the current flow
        :param lines: a list of strings, each is considered as d document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
            names defined in Protobuf. This is only used when the given ``document`` is
            a JSON string or a Python dict.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_csv
        async for r in self._get_client(**kwargs).search(
                _input_csv(lines,
                           size=size,
                           sampling_rate=sampling_rate,
                           field_resolver=field_resolver),
                on_done, on_error, on_always, data_type=DataInputType.AUTO, **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def search_lines(self,
                           lines: Union[Iterable[str], TextIO] = None,
                           filepath: str = None, size: int = None,
                           sampling_rate: float = None,
                           read_mode: str = 'r',
                           line_format: str = 'json',
                           field_resolver: Dict[str, str] = None,
                           on_done: CallbackFnType = None,
                           on_error: CallbackFnType = None,
                           on_always: CallbackFnType = None,
                           **kwargs):
        """ Use a list of files as the query source for searching on the current flow

        :param filepath: a text file that each line contains a document
        :param lines: a list of strings, each is considered as d document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param line_format: the format of each line: ``json`` or ``csv``
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
            names defined in Protobuf. This is only used when the given ``document`` is
            a JSON string or a Python dict.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_lines
        async for r in self._get_client(**kwargs).search(
                _input_lines(lines, filepath,
                             size=size,
                             sampling_rate=sampling_rate,
                             read_mode=read_mode,
                             line_format=line_format,
                             field_resolver=field_resolver),
                on_done, on_error, on_always, data_type=DataInputType.CONTENT,
                **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def index(self, input_fn: InputFnType,
                    on_done: CallbackFnType = None,
                    on_error: CallbackFnType = None,
                    on_always: CallbackFnType = None,
                    **kwargs):
        """Do indexing on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`index`.

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        async for r in self._get_client(**kwargs).index(input_fn, on_done, on_error, on_always, **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def update(self, input_fn: InputFnType,
                     on_done: CallbackFnType = None,
                     on_error: CallbackFnType = None,
                     on_always: CallbackFnType = None,
                     **kwargs):
        """Do updates on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`index`.

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        async for r in self._get_client(**kwargs).update(input_fn, on_done, on_error, on_always, **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def delete(self, ids: Iterable[str],
                     on_done: CallbackFnType = None,
                     on_error: CallbackFnType = None,
                     on_always: CallbackFnType = None,
                     **kwargs):
        """Do deletion on the current flow

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        async for r in self._get_client(**kwargs).delete(ids, on_done, on_error, on_always, **kwargs):
            yield r

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    async def search(self, input_fn: InputFnType,
                     on_done: CallbackFnType = None,
                     on_error: CallbackFnType = None,
                     on_always: CallbackFnType = None,
                     **kwargs):
        """Do searching on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`search`.

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        async for r in self._get_client(**kwargs).search(input_fn, on_done, on_error, on_always, **kwargs):
            yield r
