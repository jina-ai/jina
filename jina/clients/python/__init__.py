__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Callable, Union

from . import request
from .grpc import GrpcClient
from .helper import ProgressBar
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

    Assuming a Flow is "standby" on 192.168.1.100, with port_grpc at 55555.

    .. highlight:: python
    .. code-block:: python

        from jina.clients import py_client

        # to test connectivity
        py_client(port_grpc='192.168.1.100', host=55555).dry_run()

        # to search
        py_client(port_grpc='192.168.1.100', host=55555).search(input_fn, output_fn)

        # to index
        py_client(port_grpc='192.168.1.100', host=55555).index(input_fn, output_fn)

    """

    def __init__(self, args: 'argparse.Namespace'):
        """

        :param args: args provided by the CLI
        :param delay: if ``True`` then the client starts sending request after initializing, otherwise one needs to set
            the :attr:`input_fn` before using :func:`start` or :func:`call`
        """
        super().__init__(args)
        self._mode = self.args.mode
        self._input_fn = None

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value):
        avail = {'train', 'index', 'search'}
        if value in avail:
            self._mode = value
            self.args.mode = value
        else:
            raise ValueError(f'{value} must be one of {avail}')

    @staticmethod
    def check_input(input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None,
                    in_proto: bool = False):
        """Validate the input_fn and print the first request if success

        :param input_fn: the input function
        :param in_proto: if the input data is already in protobuf Document format, or in raw bytes
        """
        kwargs = {'data': input_fn, 'in_proto': in_proto}

        try:
            r = next(getattr(request, 'index')(**kwargs))
            default_logger.success(f'input_fn is valid and the first request is as follows:\n{r}')
        except:
            default_logger.error(f'input_fn is not valid!')
            raise

    def call_unary(self, data: Union['jina_pb2.Document', bytes], mode: str) -> None:
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

        req_iter = getattr(request, self.mode)(**kwargs)
        return self._stub.CallUnary(next(req_iter))

    def call(self, callback: Callable[['jina_pb2.Message'], None] = None, **kwargs) -> None:
        """ Calling the server, better use :func:`start` instead.

        :param callback: a callback function, invoke after every response is received
        """
        # take the default args from client
        _kwargs = vars(self.args)
        _kwargs['data'] = self.input_fn
        # override by the caller-specific kwargs
        for k in _kwargs.keys():
            if k in kwargs:
                _kwargs[k] = kwargs[k]

        tname = self.mode
        if 'mode' in kwargs:
            tname = kwargs['mode']

        req_iter = getattr(request, tname)(**_kwargs)
        # next(req_iter)

        with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
            for resp in self._stub.Call(req_iter):
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
        i.e. ``input_fn`` defined int the protobuf
        """
        if self._input_fn:
            return self._input_fn
        else:
            raise BadClient('input_fn is empty or not set')

    @input_fn.setter
    def input_fn(self, bytes_gen: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable]):
        if self._input_fn:
            self.logger.warning('input_fn is not empty, overrided')
        if hasattr(bytes_gen, '__call__'):
            self._input_fn = bytes_gen()
        else:
            self._input_fn = bytes_gen

    def dry_run(self) -> bool:
        """Send a DRYRUN request to the server, passing through all pods on the server
        useful for testing connectivity and debugging

        :return: if dry run is successful or not
        """

        def req_gen():
            req = jina_pb2.Request()
            req.control.command = jina_pb2.Request.ControlRequest.DRYRUN
            yield req

        for resp in self._stub.Call(req_gen()):
            self.logger.info(resp)
            return True

        return False

    def train(self, input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None,
              output_fn: Callable[['jina_pb2.Message'], None] = None, **kwargs):
        self.mode = 'train'
        self.input_fn = input_fn
        self.start(output_fn, **kwargs)

    def search(self, input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None,
               output_fn: Callable[['jina_pb2.Message'], None] = None, **kwargs):
        self.mode = 'search'
        self.input_fn = input_fn
        self.start(output_fn, **kwargs)

    def index(self, input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None,
              output_fn: Callable[['jina_pb2.Message'], None] = None, **kwargs):
        self.mode = 'index'
        self.input_fn = input_fn
        self.start(output_fn, **kwargs)
