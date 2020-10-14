__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import time
from typing import Iterator, Callable, Union, Tuple

from . import request
from .grpc import GrpcClient
from .helper import ProgressBar
from ...enums import ClientMode
from ...excepts import BadClient
from ...logging import default_logger
from ...logging.profile import TimeContext
from ...proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class PyClient(GrpcClient):
    """A simple Python client for connecting to the gateway. This class is for internal only,
    use the python interface :func:`jina.clients.py_client` to start :class:`PyClient` if you
    want to use it in Python.

    Assuming a Flow is "standby" on 192.168.1.100, with port_expose at 55555.

    .. highlight:: python
    .. code-block:: python

        from jina.clients import py_client

        # to test connectivity
        py_client(host='192.168.1.100', port_expose=55555).dry_run()

        # to search
        py_client(host='192.168.1.100', port_expose=55555).search(input_fn, output_fn)

        # to index
        py_client(host='192.168.1.100', port_expose=55555).index(input_fn, output_fn)

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
    def mode(self, value: ClientMode) -> None:
        if isinstance(value, ClientMode):
            self._mode = value
            self.args.mode = value
        else:
            raise ValueError(f'{value} must be one of {ClientMode}')

    @staticmethod
    def check_input(input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None) -> None:
        """Validate the input_fn and print the first request if success

        :param input_fn: the input function
        """
        if hasattr(input_fn, '__call__'):
            input_fn = input_fn()

        kwargs = {'data': input_fn}

        try:
            r = next(getattr(request, 'index')(**kwargs))
            if r is not None:
                default_logger.success(f'input_fn is valid')
            else:
                raise TypeError
        except:
            default_logger.error(f'input_fn is not valid!')
            raise

    def call_unary(self, data: Union['jina_pb2.Document', bytes], mode: ClientMode) -> None:
        """ Calling the server with one request only, and return the result

        This function should not be used in production due to its low-efficiency. For example,
        you should not use it in a for-loop. Use :meth:`call` instead.
        Nonetheless, you can use it for testing one query and check the result.

        :param data: the binary data of the document or the ``Document`` in protobuf
        :param mode: request will be sent in this mode, available ``train``, ``index``, ``query``
        """
        self.mode = mode
        kwargs = vars(self.args)
        kwargs['data'] = [data]

        req_iter = getattr(request, str(self.mode).lower())(**kwargs)
        return self._stub.CallUnary(next(req_iter))

    def call(self, callback: Callable[['jina_pb2.Message'], None] = None, **kwargs) -> None:
        """ Calling the server, better use :func:`start` instead.

        :param callback: a callback function, invoke after every response is received
        """
        # take the default args from client
        _kwargs = vars(self.args)
        _kwargs['data'] = self.input_fn
        # override by the caller-specific kwargs
        _kwargs.update(kwargs)

        tname = str(self.mode).lower()
        if 'mode' in kwargs:
            tname = str(kwargs['mode']).lower()

        req_iter = getattr(request, tname)(**_kwargs)

        with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
            for resp in self._stub.Call(req_iter):
                if resp.status.code >= jina_pb2.Status.ERROR:
                    self.logger.error(f'callback() may not work properly '
                                      f'due to the bad response: {resp.status.description}')
                    self.logger.error(resp.status.details)
                if callback:
                    try:
                        if self.args.callback_on_body:
                            resp = getattr(resp, resp.WhichOneof('body'))
                        callback(resp)
                    except Exception as ex:
                        raise BadClient('error in client\'s callback: %s' % ex)
                p_bar.update(self.args.batch_size)

    @property
    def input_fn(self) -> Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable]:
        """ An iterator of bytes, each element represents a document's raw content,
        i.e. ``input_fn`` defined in the protobuf
        """
        if self._input_fn is not None:
            return self._input_fn
        else:
            raise BadClient('input_fn is empty or not set')

    @input_fn.setter
    def input_fn(self, bytes_gen: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable]) -> None:
        if self._input_fn:
            self.logger.warning('input_fn is not empty, overrided')
        if hasattr(bytes_gen, '__call__'):
            self._input_fn = bytes_gen()
        else:
            self._input_fn = bytes_gen

    def dry_run(self, as_request: str) -> bool:
        """A dry run request is a Search/Index/Train Request with empty content.
        Useful for testing connectivity and debugging the connectivity of the server/flow

        :param as_request: send the dry run request as one of 'index', 'search', 'train', 'control' request
        :return: if dry run is successful or not
        """

        def req_gen():
            req = jina_pb2.Request()
            if as_request == 'train':
                req.train.CopyFrom(jina_pb2.Request.TrainRequest())
            elif as_request == 'index':
                req.index.CopyFrom(jina_pb2.Request.IndexRequest())
            elif as_request == 'search':
                req.search.CopyFrom(jina_pb2.Request.SearchRequest())
            elif as_request == 'evaluate':
                req.evaluate.CopyFrom(jina_pb2.Request.EvaluateRequest())
            elif as_request == 'control':
                req.control.CopyFrom(jina_pb2.Request.ControlRequest())
            else:
                raise ValueError(
                    f'as_request={as_request} is not supported, must be one of "train", "search", "index", "control"')
            yield req

        before = time.perf_counter()
        for resp in self._stub.Call(req_gen()):
            if resp.status.code < jina_pb2.Status.ERROR:
                self.logger.info(
                    f'dry run of {as_request} takes {time.perf_counter() - before:.3f}s, this flow has a good connectivity')
                return True
            else:
                self.logger.error(resp.status)

        return False

    def train(self, input_fn: Union[Iterator[Union['jina_pb2.Document', bytes]], Callable] = None,
              output_fn: Callable[['jina_pb2.Message'], None] = None, **kwargs) -> None:
        self.mode = ClientMode.TRAIN
        self.input_fn = input_fn
        if not self.args.skip_dry_run:
            self.dry_run(as_request='train')
        self.start(output_fn, **kwargs)

    def search(self, input_fn: Union[Iterator[Union['jina_pb2.Document', bytes]], Callable] = None,
               output_fn: Callable[['jina_pb2.Message'], None] = None, **kwargs) -> None:
        self.mode = ClientMode.SEARCH
        self.input_fn = input_fn
        if not self.args.skip_dry_run:
            self.dry_run(as_request='search')
        self.start(output_fn, **kwargs)

    def index(self, input_fn: Union[Iterator[Union['jina_pb2.Document', bytes]], Callable]= None,
              output_fn: Callable[['jina_pb2.Message'], None] = None, **kwargs) -> None:
        self.mode = ClientMode.INDEX
        self.input_fn = input_fn
        if not self.args.skip_dry_run:
            self.dry_run(as_request='index')
        self.start(output_fn, **kwargs)

    def evaluate(self, input_fn: Union[Iterator[Tuple[Union['jina_pb2.Document', bytes], Union['jina_pb2.Document', bytes]]], Callable] = None,
                 output_fn: Callable[['jina_pb2.Message'], None] = None, **kwargs) -> None:
        self.mode = ClientMode.EVALUATE
        self.input_fn = input_fn
        if not self.args.skip_dry_run:
            self.dry_run(as_request='evaluate')
        self.start(output_fn, **kwargs)
