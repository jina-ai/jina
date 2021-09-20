import asyncio
from contextlib import nullcontext
from typing import Callable, Optional

from ..base import BaseClient, InputType
from ..helper import callback_exec
from ...excepts import BadClient
from ...importer import ImportExtensions
from ...logging.profile import ProgressBar
from ...types.request import Request


class HTTPBaseClient(BaseClient):
    """A MixIn for HTTP Client."""

    async def _get_http_response(self, session, dest_url, req_dict):
        async with session.post(
            dest_url,
            json=req_dict,
        ) as response:
            resp_str = await response.json()
            return response.status, resp_str

    async def _get_results(
        self,
        inputs: InputType,
        on_done: Callable,
        on_error: Optional[Callable] = None,
        on_always: Optional[Callable] = None,
        **kwargs,
    ):
        """
        :meth:`send_requests()`
            Traverses through the request iterator
            Sends each request & awaits :meth:`websocket.send()`
            Sends & awaits `byte(True)` to acknowledge request iterator is empty
        Traversal logic:
            Starts an independent task :meth:`send_requests()`
            Awaits on each response from :meth:`websocket.recv()` (done in an async loop)
            This makes sure client makes concurrent invocations
        Await exit strategy:
            :meth:`send_requests()` keeps track of num_requests sent
            Async recv loop keeps track of num_responses received
            Client exits out of await when num_requests == num_responses

        :param inputs: the callable
        :param on_done: the callback for on_done
        :param on_error: the callback for on_error
        :param on_always: the callback for on_always
        :param kwargs: kwargs for _get_task_name and _get_requests
        :yields: generator over results
        """
        with ImportExtensions(required=True):
            import aiohttp

        self.inputs = inputs

        req_iter = self._get_requests(**kwargs)
        async with aiohttp.ClientSession() as session:

            try:
                cm1 = ProgressBar() if self.show_progress else nullcontext()
                proto = 'https' if self.args.https else 'http'
                url = f'{proto}://{self.args.host}:{self.args.port}/post'

                with cm1 as p_bar:
                    all_responses = []
                    for req in req_iter:
                        # fix the mismatch between pydantic model and Protobuf model
                        req_dict = req.dict()
                        req_dict['exec_endpoint'] = req_dict['header']['exec_endpoint']
                        req_dict['data'] = req_dict['data'].get('docs', None)

                        all_responses.append(
                            asyncio.create_task(
                                self._get_http_response(
                                    session,
                                    url,
                                    req_dict,
                                )
                            )
                        )

                    for resp in asyncio.as_completed(all_responses):
                        r_status, r_str = await resp
                        if r_status == 404:
                            raise BadClient(f'no such endpoint {url}')
                        elif r_status < 200 or r_status > 300:
                            raise ValueError(r_str)

                        resp = Request(r_str)
                        resp = resp.as_typed_request(resp.request_type).as_response()
                        callback_exec(
                            response=resp,
                            on_error=on_error,
                            on_done=on_done,
                            on_always=on_always,
                            continue_on_error=self.continue_on_error,
                            logger=self.logger,
                        )
                        if self.show_progress:
                            p_bar.update()
                        yield resp
            except aiohttp.client_exceptions.ClientConnectorError:
                self.logger.warning(f'Client got disconnected from the HTTP server')
