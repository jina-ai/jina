import uuid
from typing import Union, List, Iterator, Dict

import numpy as np

from .base import BaseFlow
from ..clients.base import InputFnType, CallbackFnType
from ..enums import DataInputType


class Flow(BaseFlow):

    def train(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
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
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        return self._get_client(**kwargs).train(input_fn, on_done, on_error, on_always, **kwargs)

    def index_ndarray(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
                      on_done: CallbackFnType = None,
                      on_error: CallbackFnType = None,
                      on_always: CallbackFnType = None,
                      **kwargs):
        """Using numpy ndarray as the index source for the current flow

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the the numpy data source beforehand
        :param on_done: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_ndarray
        return self._get_client(**kwargs).index(_input_ndarray(array, axis, size, shuffle),
                                                on_done, on_error, on_always, data_type=DataInputType.CONTENT, **kwargs)

    def search_ndarray(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
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
        self._get_client(**kwargs).search(_input_ndarray(array, axis, size, shuffle),
                                          on_done, on_error, on_always, data_type=DataInputType.CONTENT, **kwargs)

    def index_lines(self, lines: Iterator[str] = None, filepath: str = None, size: int = None,
                    sampling_rate: float = None, read_mode='r',
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
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_lines
        return self._get_client(**kwargs).index(_input_lines(lines, filepath, size, sampling_rate, read_mode),
                                                on_done, on_error, on_always, data_type=DataInputType.CONTENT, **kwargs)

    def index_files(self, patterns: Union[str, List[str]], recursive: bool = True,
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
        return self._get_client(**kwargs).index(_input_files(patterns, recursive, size, sampling_rate, read_mode),
                                                on_done, on_error, on_always, data_type=DataInputType.CONTENT, **kwargs)

    def search_files(self, patterns: Union[str, List[str]], recursive: bool = True,
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
        return self._get_client(**kwargs).search(_input_files(patterns, recursive, size, sampling_rate, read_mode),
                                                 on_done, on_error, on_always, data_type=DataInputType.CONTENT,
                                                 **kwargs)

    def search_lines(self, filepath: str = None, lines: Iterator[str] = None, size: int = None,
                     sampling_rate: float = None, read_mode='r',
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
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.sugary_io import _input_lines
        return self._get_client(**kwargs).search(_input_lines(lines, filepath, size, sampling_rate, read_mode),
                                                 on_done, on_error, on_always, data_type=DataInputType.CONTENT,
                                                 **kwargs)

    def index(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
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
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        return self._get_client(**kwargs).index(input_fn, on_done, on_error, on_always, **kwargs)

    def update(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
               **kwargs):
        """Updates documents on the current flow
        Example,
        .. highlight:: python
        .. code-block:: python
            with f:
                f.update(input_fn)
                ...
        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.
        One may also build a reader/generator on your own.
        Example,
        .. highlight:: python
        .. code-block:: python
            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'  # each yield generates a document to update
            with f.build(runtime='thread') as flow:
                flow.update(bytes_gen=my_reader())
        It will start a :py:class:`CLIClient` and call :py:func:`update`.
        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(**kwargs).update(input_fn, on_done, on_error, on_always, **kwargs)

    def delete(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
               **kwargs):
        """Do deletion on the current flow
        Example,
        .. highlight:: python
        .. code-block:: python
            with f:
                f.delete(input_fn)
                ...
        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.
        One may also build a reader/generator on your own.
        Example,
        .. highlight:: python
        .. code-block:: python
            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'  # each yield generates a document to delete
            with f.build(runtime='thread') as flow:
                flow.delete(bytes_gen=my_reader())
        It will start a :py:class:`CLIClient` and call :py:func:`delete`.
        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(**kwargs).delete(input_fn, on_done, on_error, on_always, **kwargs)

    def search(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
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
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        return self._get_client(**kwargs).search(input_fn, on_done, on_error, on_always, **kwargs)

    @property
    def workspace_id(self) -> Dict[str, str]:
        """Get all Pods' ``workspace_id`` values in a dict """
        return {k: p.args.workspace_id for k, p in self if hasattr(p.args, 'workspace_id')}

    @workspace_id.setter
    def workspace_id(self, value: str):
        """Set all Pods' ``workspace_id`` to ``value``

        :param value: a hexadecimal UUID string
        """
        uuid.UUID(value)
        for k, p in self:
            if hasattr(p.args, 'workspace_id'):
                p.args.workspace_id = value
