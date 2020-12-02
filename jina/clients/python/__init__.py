__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import time
from typing import Callable, Union, Optional, Dict

from . import request
from .grpc import AsyncGrpcClient
from .helper import ProgressBar, pprint_routes, safe_callback, extract_field
from .request import GeneratorSourceType
from ...enums import RequestType
from ...excepts import BadClient, DryRunException
from ...helper import typename
from ...logging import default_logger
from ...logging.profile import TimeContext
from ...proto import jina_pb2
from ...types.request import Request
from ...types.request.common import DryRunRequest, TrainDryRunRequest, IndexDryRunRequest, SearchDryRunRequest

InputFnType = Union[GeneratorSourceType, Callable[..., GeneratorSourceType]]

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class PyClient(AsyncGrpcClient):
    """A simple Python client for connecting to the gateway. This class is for internal only,
    use the python interface :func:`jina.clients.py_client` to start :class:`PyClient` if you
    want to use it in Python.

    Assuming a Flow is "standby" on 192.168.1.100, with port_expose at 55555.

    .. highlight:: python
    .. code-block:: python

        from jina.clients import py_client

        # to test connectivity
        await py_client(host='192.168.1.100', port_expose=55555).dry_run()

        # to search
        await py_client(host='192.168.1.100', port_expose=55555).search(input_fn, output_fn)

        # to index
        await py_client(host='192.168.1.100', port_expose=55555).index(input_fn, output_fn)

    .. note::
        to perform `index`, `search` or `train`, py_client needs to be awaited, as it is a coroutine

    """

    def __init__(self, args: 'argparse.Namespace'):
        """

        :param args: args provided by the CLI

        """
        super().__init__(args)
        self._mode = self.args.mode
        self._input_fn = None

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: RequestType) -> None:
        if isinstance(value, RequestType):
            self._mode = value
            self.args.mode = value
        else:
            raise ValueError(f'{value} must be one of {RequestType}')

    @staticmethod
    def check_input(input_fn: Optional[InputFnType] = None, **kwargs) -> None:
        """Validate the input_fn and print the first request if success

        :param input_fn: the input function
        """
        if hasattr(input_fn, '__call__'):
            input_fn = input_fn()

        kwargs['data'] = input_fn

        try:
            r = next(getattr(request, 'index')(**kwargs))
            if r is not None:
                default_logger.success(f'input_fn is valid')
            else:
                raise TypeError
        except:
            default_logger.error(f'input_fn is not valid!')
            raise

    async def call_unary(self, data: Union[GeneratorSourceType], mode: RequestType, **kwargs) -> None:
        """ Calling the server with one request only, and return the result

        This function should not be used in production due to its low-efficiency. For example,
        you should not use it in a for-loop. Use :meth:`call` instead.
        Nonetheless, you can use it for testing one query and check the result.

        :param data: the binary data of the document in protobuf
        :param mode: request will be sent in this mode, available ``train``, ``index``, ``query``
        """
        self.mode = mode
        # take the default args from client
        _kwargs = vars(self.args)
        _kwargs['data'] = data
        # override by the caller-specific kwargs
        _kwargs.update(kwargs)

        req_iter = getattr(request, str(self.mode).lower())(**_kwargs)
        return await self._stub.CallUnary(next(req_iter))

    async def call(self,
                   on_done: Callable[['Request'], None] = None,
                   on_error: Callable[['Request'], None] = pprint_routes,
                   on_always: Callable[['Request'], None] = None,
                   **kwargs) -> None:
        """ Calling the server with promise callbacks, better use :func:`start` instead.

        :param on_done: a callback function, invoke after every success response is received
        :param on_error: a callback function on error, invoke on every error response
        :param on_always: a callback function when a request is complete
        """
        # take the default args from client
        _kwargs = vars(self.args)
        _kwargs['data'] = self.input_fn
        # override by the caller-specific kwargs
        _kwargs.update(kwargs)

        tname = str(self.mode).lower()
        if 'mode' in kwargs:
            tname = str(kwargs['mode']).lower()

        if on_error:
            safe_on_error = safe_callback(on_error, self.args.continue_on_error, self.logger)

        if on_done:
            safe_on_done = safe_callback(on_done, self.args.continue_on_error, self.logger)

        if on_always:
            safe_on_always = safe_callback(on_always, self.args.continue_on_error, self.logger)

        req_iter = getattr(request, tname)(**_kwargs)

        with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
            async for resp in self._stub.Call(req_iter):
                if resp.status.code >= jina_pb2.StatusProto.ERROR and on_error:
                    safe_on_error(resp)
                elif on_done:
                    safe_on_done(resp)
                if on_always:
                    safe_on_always(resp)
                p_bar.update(self.args.batch_size)

    @property
    def input_fn(self) -> InputFnType:
        """ An iterator of bytes, each element represents a document's raw content,
        i.e. ``input_fn`` defined in the protobuf
        """
        if self._input_fn is not None:
            return self._input_fn
        else:
            raise BadClient('input_fn is empty or not set')

    @input_fn.setter
    def input_fn(self, bytes_gen: InputFnType) -> None:
        if self._input_fn:
            self.logger.warning('input_fn is not empty, overrided')
        if hasattr(bytes_gen, '__call__'):
            self._input_fn = bytes_gen()
        else:
            self._input_fn = bytes_gen

    async def dry_run(self, req: 'DryRunRequest') -> None:
        """A dry run request is a Search/Index/Train Request with empty content.
        Useful for testing connectivity and debugging the connectivity of the server/flow

        :param req: send the dry run request as one of 'index', 'search', 'train', 'control' request
        :return: if dry run is successful or not
        """

        def req_gen():
            yield req

        before = time.perf_counter()
        async for resp in self._stub.Call(req_gen()):
            if resp.status.code < jina_pb2.StatusProto.ERROR:
                self.logger.info(
                    f'dry run of {typename(req)} takes {time.perf_counter() - before:.3f}s, '
                    f'this flow has a good connectivity')
            else:
                raise DryRunException(resp.status)

    async def train(self, input_fn: Optional[InputFnType] = None,
                    output_fn: Callable[['Request'], None] = None, **kwargs) -> None:
        self.mode = RequestType.TRAIN
        self.input_fn = input_fn
        if not self.args.skip_dry_run:
            await self.dry_run(TrainDryRunRequest())
        await self.start(output_fn, **kwargs)

    async def search(self, input_fn: Optional[InputFnType] = None,
                     output_fn: Callable[['Request'], None] = None, **kwargs) -> None:
        self.mode = RequestType.SEARCH
        self.input_fn = input_fn
        if not self.args.skip_dry_run:
            await self.dry_run(SearchDryRunRequest())
        await self.start(output_fn, **kwargs)

    async def index(self, input_fn: Optional[InputFnType] = None,
                    output_fn: Callable[['Request'], None] = None, **kwargs) -> None:
        self.mode = RequestType.INDEX
        self.input_fn = input_fn
        if not self.args.skip_dry_run:
            await self.dry_run(IndexDryRunRequest())
        await self.start(output_fn, **kwargs)
