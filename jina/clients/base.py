__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import os
from typing import Callable, Union, Optional, Iterator, List

import grpc

from . import request
from .helper import callback_exec
from .request import GeneratorSourceType
from ..enums import RequestType
from ..excepts import BadClient, BadClientInput
from ..helper import typename
from ..logging import default_logger, JinaLogger
from ..logging.profile import TimeContext, ProgressBar
from ..proto import jina_pb2_grpc
from ..types.request import Request, Response

InputFnType = Union[GeneratorSourceType, Callable[..., GeneratorSourceType]]
CallbackFnType = Optional[Callable[..., None]]


class BaseClient:
    """A base client for connecting to the gateway.

    .. note::
        :class:`BaseClient` does not provide `train`, `index`, `search` interfaces.
        Please use :class:`Client` or :class:`AsyncClient`.
    """

    def __init__(self, args: 'argparse.Namespace'):
        """
        :param args: args provided by the CLI
        """
        self.args = args
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))

        if not args.proxy and os.name != 'nt':
            # (Han 2020 12.12): gRPC channel is over HTTP2 and it does not work when we have proxy
            # as many enterprise users are behind proxy, a quick way to
            # surpass it is by temporally unset proxy. Please do NOT panic as it will NOT
            # affect users os-level envs.
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self._mode = args.mode
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
            if isinstance(r, Request):
                default_logger.success(f'input_fn is valid')
            else:
                raise TypeError(f'{typename(r)} is not a valid Request')
        except Exception as ex:
            default_logger.error(f'input_fn is not valid!')
            raise BadClientInput from ex

    def _get_requests(self, **kwargs) -> Iterator['Request']:
        """Get request in generator"""
        _kwargs = vars(self.args)
        _kwargs['data'] = self.input_fn
        # override by the caller-specific kwargs
        _kwargs.update(kwargs)

        tname = str(self.mode).lower()
        if 'mode' in kwargs:
            tname = str(kwargs['mode']).lower()

        return getattr(request, tname)(**_kwargs), tname

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
        if hasattr(bytes_gen, '__call__'):
            self._input_fn = bytes_gen()
        else:
            self._input_fn = bytes_gen

    async def _get_results(self,
                           input_fn: Callable,
                           on_done: Callable,
                           on_error: Callable = None,
                           on_always: Callable = None, **kwargs):
        result = []  # type: List['Response']
        try:
            self.input_fn = input_fn
            req_iter, tname = self._get_requests(**kwargs)
            async with grpc.aio.insecure_channel(f'{self.args.host}:{self.args.port_expose}',
                                                 options=[('grpc.max_send_message_length', -1),
                                                          ('grpc.max_receive_message_length', -1)]) as channel:
                stub = jina_pb2_grpc.JinaRPCStub(channel)
                self.logger.success(f'connected to the gateway at {self.args.host}:{self.args.port_expose}!')
                with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
                    async for response in stub.Call(req_iter):
                        resp = response.to_response()
                        if self.args.return_results:
                            result.append(resp)
                        callback_exec(response=resp,
                                      on_error=on_error,
                                      on_done=on_done,
                                      on_always=on_always,
                                      continue_on_error=self.args.continue_on_error,
                                      logger=self.logger)
                        p_bar.update(self.args.request_size)
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except grpc.aio._call.AioRpcError as rpc_ex:
            # Since this object is guaranteed to be a grpc.Call, might as well include that in its name.
            my_code = rpc_ex.code()
            my_details = rpc_ex.details()
            msg = f'gRPC error: {my_code} {my_details}'
            if my_code == grpc.StatusCode.UNAVAILABLE:
                self.logger.error(
                    f'{msg}\nthe ongoing request is terminated as the server is not available or closed already')
                raise rpc_ex
            elif my_code == grpc.StatusCode.INTERNAL:
                self.logger.error(f'{msg}\ninternal error on the server side')
                raise rpc_ex
            elif my_code == grpc.StatusCode.UNKNOWN and 'asyncio.exceptions.TimeoutError' in my_details:
                raise BadClientInput(f'{msg}\n'
                                     'often the case is that you define/send a bad input iterator to jina, '
                                     'please double check your input iterator') from rpc_ex
            else:
                raise BadClient(msg) from rpc_ex
        if self.args.return_results:
            return result

    def index(self):
        raise NotImplementedError

    def search(self):
        raise NotImplementedError

    def train(self):
        raise NotImplementedError
