"""Module containing the Base Client for Jina."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import os
from typing import Callable, Union, Optional, Iterator, Dict, AsyncIterator
import asyncio

import grpc
import inspect
from .helper import callback_exec
from .request import GeneratorSourceType
from ..enums import RequestType
from ..excepts import BadClient, BadClientInput
from ..helper import typename
from ..logging import default_logger, JinaLogger
from ..logging.profile import TimeContext, ProgressBar
from ..proto import jina_pb2_grpc
from ..types.request import Request

InputType = Union[GeneratorSourceType, Callable[..., GeneratorSourceType]]
CallbackFnType = Optional[Callable[..., None]]


class BaseClient:
    """A base client for connecting to the Flow Gateway.

    .. note::
        :class:`BaseClient` does not provide `train`, `index`, `search` interfaces.
        Please use :class:`Client` or :class:`AsyncClient`.

    :param args: the Namespace from argparse
    """

    def __init__(self, args: 'argparse.Namespace'):
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
        self._inputs = None

    @property
    def mode(self) -> str:
        """
        Get the mode for this client (index, query etc.).

        :return: Mode of the client.
        """
        return self._mode

    @mode.setter
    def mode(self, value: RequestType) -> None:
        """
        Set the mode.

        :param value: Request type. (e.g. INDEX, SEARCH, DELETE, UPDATE, CONTROL, TRAIN)
        """
        if isinstance(value, RequestType):
            self._mode = value
            self.args.mode = value
        else:
            raise ValueError(f'{value} must be one of {RequestType}')

    @staticmethod
    def check_input(inputs: Optional[InputType] = None, **kwargs) -> None:
        """Validate the inputs and print the first request if success.

        :param inputs: the inputs
        :param kwargs: keyword arguments
        """
        if hasattr(inputs, '__call__'):
            # it is a function
            inputs = inputs()

        kwargs['data'] = inputs

        if inspect.isasyncgenfunction(inputs) or inspect.isasyncgen(inputs):
            raise NotImplementedError(
                'checking the validity of an async generator is not implemented yet'
            )

        try:
            from .request import request_generator

            r = next(request_generator(**kwargs))
            if isinstance(r, Request):
                default_logger.success(f'inputs is valid')
            else:
                raise TypeError(f'{typename(r)} is not a valid Request')
        except Exception as ex:
            default_logger.error(f'inputs is not valid!')
            raise BadClientInput from ex

    def _get_requests(
        self, **kwargs
    ) -> Union[Iterator['Request'], AsyncIterator['Request']]:
        """
        Get request in generator.

        :param kwargs: Keyword arguments.
        :return: Iterator of request.
        """
        _kwargs = vars(self.args)
        _kwargs['data'] = self.inputs
        # override by the caller-specific kwargs
        _kwargs.update(kwargs)

        if inspect.isasyncgen(self.inputs):
            from .request.asyncio import request_generator

            return request_generator(**_kwargs)
        else:
            from .request import request_generator

            return request_generator(**_kwargs)

    def _get_task_name(self, kwargs: Dict) -> str:
        tname = str(self.mode).lower()
        if 'mode' in kwargs:
            tname = str(kwargs['mode']).lower()
        return tname

    @property
    def inputs(self) -> InputType:
        """
        An iterator of bytes, each element represents a Document's raw content.

        ``inputs`` defined in the protobuf

        :return: inputs
        """
        if self._inputs is not None:
            return self._inputs
        else:
            raise BadClient('inputs are not defined')

    @inputs.setter
    def inputs(self, bytes_gen: InputType) -> None:
        """
        Set the input data.

        :param bytes_gen: input type
        """
        if hasattr(bytes_gen, '__call__'):
            self._inputs = bytes_gen()
        else:
            self._inputs = bytes_gen

    async def _get_results(
        self,
        inputs: InputType,
        on_done: Callable,
        on_error: Callable = None,
        on_always: Callable = None,
        **kwargs,
    ):
        try:
            self.inputs = inputs
            tname = self._get_task_name(kwargs)
            req_iter = self._get_requests(**kwargs)
            async with grpc.aio.insecure_channel(
                f'{self.args.host}:{self.args.port_expose}',
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            ) as channel:
                stub = jina_pb2_grpc.JinaRPCStub(channel)
                self.logger.success(
                    f'connected to the gateway at {self.args.host}:{self.args.port_expose}!'
                )
                with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
                    async for resp in stub.Call(req_iter):
                        resp.as_typed_request(resp.request_type)
                        resp.as_response()
                        callback_exec(
                            response=resp,
                            on_error=on_error,
                            on_done=on_done,
                            on_always=on_always,
                            continue_on_error=self.args.continue_on_error,
                            logger=self.logger,
                        )
                        p_bar.update(self.args.request_size)
                        yield resp
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except asyncio.CancelledError as ex:
            self.logger.warning(f'process error: {ex!r}, terminate signal send?')
        except grpc.aio._call.AioRpcError as rpc_ex:
            # Since this object is guaranteed to be a grpc.Call, might as well include that in its name.
            my_code = rpc_ex.code()
            my_details = rpc_ex.details()
            msg = f'gRPC error: {my_code} {my_details}'
            if my_code == grpc.StatusCode.UNAVAILABLE:
                self.logger.error(
                    f'{msg}\nthe ongoing request is terminated as the server is not available or closed already'
                )
                raise rpc_ex
            elif my_code == grpc.StatusCode.INTERNAL:
                self.logger.error(f'{msg}\ninternal error on the server side')
                raise rpc_ex
            elif (
                my_code == grpc.StatusCode.UNKNOWN
                and 'asyncio.exceptions.TimeoutError' in my_details
            ):
                raise BadClientInput(
                    f'{msg}\n'
                    'often the case is that you define/send a bad input iterator to jina, '
                    'please double check your input iterator'
                ) from rpc_ex
            else:
                raise BadClient(msg) from rpc_ex

    def index(self):
        """Issue 'index' request to the Flow."""
        raise NotImplementedError

    def search(self):
        """Issue 'search' request to the Flow."""
        raise NotImplementedError

    def train(self):
        """Issue 'train' request to the Flow."""
        raise NotImplementedError

    @staticmethod
    def add_default_kwargs(kwargs: Dict):
        """
        Add the default kwargs to the instance.

        :param kwargs: the kwargs to add
        """
        # TODO: refactor it into load from config file
        if ('top_k' in kwargs) and (kwargs['top_k'] is not None):
            # associate all VectorSearchDriver and SliceQL driver to use top_k
            from jina import QueryLang

            topk_ql = [
                QueryLang(
                    {
                        'name': 'SliceQL',
                        'priority': 1,
                        'parameters': {'end': kwargs['top_k']},
                    }
                ),
                QueryLang(
                    {
                        'name': 'VectorSearchDriver',
                        'priority': 1,
                        'parameters': {'top_k': kwargs['top_k']},
                    }
                ),
            ]
            if 'queryset' not in kwargs:
                kwargs['queryset'] = topk_ql
            else:
                kwargs['queryset'].extend(topk_ql)
