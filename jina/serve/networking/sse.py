# Copyright © 2020, [sysid](https://sysid.github.io/).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import enum
import io
import json
import logging
import re
from datetime import datetime
from functools import partial
from typing import Any, AsyncIterable, Callable, Coroutine, Dict, Optional, Union

import anyio
from starlette.background import BackgroundTask
from starlette.concurrency import iterate_in_threadpool
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

_log = logging.getLogger(__name__)


# https://stackoverflow.com/questions/58133694/graceful-shutdown-of-uvicorn-starlette-app-with-websockets
class AppStatus:
    """helper for monkey-patching the signal-handler of uvicorn"""

    should_exit = False
    should_exit_event: Union[anyio.Event, None] = None

    @staticmethod
    def handle_exit(*args, **kwargs):
        # set bool flag before checking the event to avoid race condition
        AppStatus.should_exit = True
        # Check if event has been initialized, if so notify listeners
        if AppStatus.should_exit_event is not None:
            AppStatus.should_exit_event.set()
        original_handler(*args, **kwargs)


try:
    from uvicorn.main import Server

    original_handler = Server.handle_exit
    Server.handle_exit = AppStatus.handle_exit  # type: ignore

    def unpatch_uvicorn_signal_handler():
        """restores original signal-handler and rolls back monkey-patching.
        Normally this should not be necessary.
        """
        Server.handle_exit = original_handler

except ModuleNotFoundError:
    _log.debug("Uvicorn not used.")


class SseState(enum.Enum):
    CONNECTING = 0
    OPENED = 1
    CLOSED = 2


class ServerSentEvent:
    def __init__(
        self,
        data: Optional[Any] = None,
        *,
        event: Optional[str] = None,
        id: Optional[int] = None,
        retry: Optional[int] = None,
        comment: Optional[str] = None,
        sep: Optional[str] = None,
    ) -> None:
        """Send data using EventSource protocol

        :param str data: The data field for the message.
        :param str id: The event ID to set the EventSource object's last
            event ID value to.
        :param str event: The event's type. If this is specified, an event will
            be dispatched on the browser to the listener for the specified
            event name; the web site would use addEventListener() to listen
            for named events. The default event type is "message".
        :param int retry: The reconnection time to use when attempting to send
            the event. [What code handles this?] This must be an integer,
            specifying the reconnection time in milliseconds. If a non-integer
            value is specified, the field is ignored.
        :param str comment: A colon as the first character of a line is essence
            a comment, and is ignored. Usually used as a ping message to keep connecting.
            If set, this will be a comment message.
        """
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry
        self.comment = comment
        self.DEFAULT_SEPARATOR = "\r\n"
        self.LINE_SEP_EXPR = re.compile(r"\r\n|\r|\n")
        self._sep = sep if sep is not None else self.DEFAULT_SEPARATOR

    def encode(self) -> bytes:
        buffer = io.StringIO()
        if self.comment is not None:
            for chunk in self.LINE_SEP_EXPR.split(str(self.comment)):
                buffer.write(f": {chunk}")
                buffer.write(self._sep)

        if self.id is not None:
            buffer.write(self.LINE_SEP_EXPR.sub("", f"id: {self.id}"))
            buffer.write(self._sep)

        if self.event is not None:
            buffer.write(self.LINE_SEP_EXPR.sub("", f"event: {self.event}"))
            buffer.write(self._sep)

        if self.data is not None:
            for chunk in self.LINE_SEP_EXPR.split(json.dumps(self.data)):
                buffer.write(f"data: {chunk}")
                buffer.write(self._sep)

        if self.retry is not None:
            if not isinstance(self.retry, int):
                raise TypeError("retry argument must be int")
            buffer.write(f"retry: {self.retry}")
            buffer.write(self._sep)

        buffer.write(self._sep)
        return buffer.getvalue().encode("utf-8")


def ensure_bytes(data: Union[bytes, dict, ServerSentEvent, Any]) -> bytes:
    if isinstance(data, bytes):
        return data
    elif isinstance(data, ServerSentEvent):
        return data.encode()
    elif isinstance(data, dict):
        return ServerSentEvent(**data).encode()
    else:
        return ServerSentEvent(str(data)).encode()


class EventSourceResponse(Response):
    """Implements the ServerSentEvent Protocol:
    https://www.w3.org/TR/2009/WD-eventsource-20090421/

    Responses must not be compressed by middleware in order to work.
    implementation based on Starlette StreamingResponse
    """

    DEFAULT_PING_INTERVAL = 15

    # noinspection PyMissingConstructor
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict] = None,
        media_type: str = "text/event-stream",
        background: Optional[BackgroundTask] = None,
        ping: Optional[int] = None,
        sep: Optional[str] = None,
        ping_message_factory: Optional[Callable[[], ServerSentEvent]] = None,
        data_sender_callable: Optional[
            Callable[[], Coroutine[None, None, None]]
        ] = None,
    ) -> None:
        self.sep = sep
        self.ping_message_factory = ping_message_factory
        if isinstance(content, AsyncIterable):
            self.body_iterator = (
                content
            )  # type: AsyncIterable[Union[Any,dict,ServerSentEvent]]
        else:
            self.body_iterator = iterate_in_threadpool(content)  # type: ignore
        self.status_code = status_code
        self.media_type = self.media_type if media_type is None else media_type
        self.background = background  # type: ignore  # follows https://github.com/encode/starlette/blob/master/starlette/responses.py
        self.data_sender_callable = data_sender_callable

        _headers = {}
        if headers is not None:  # pragma: no cover
            _headers.update(headers)

        # mandatory for servers-sent events headers
        # allow cache control header to be set by user to support fan out proxies
        # https://www.fastly.com/blog/server-sent-events-fastly
        _headers.setdefault("Cache-Control", "no-cache")
        _headers["Connection"] = "keep-alive"
        _headers["X-Accel-Buffering"] = "no"

        self.init_headers(_headers)

        self.ping_interval = self.DEFAULT_PING_INTERVAL if ping is None else ping
        self.active = True

        self._ping_task = None
        self._send_lock = anyio.Lock()

    @staticmethod
    async def listen_for_disconnect(receive: Receive) -> None:
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                _log.debug("Got event: http.disconnect. Stop streaming.")
                break

    @staticmethod
    async def listen_for_exit_signal() -> None:
        # Check if should_exit was set before anybody started waiting
        if AppStatus.should_exit:
            return

        # Setup an Event
        if AppStatus.should_exit_event is None:
            AppStatus.should_exit_event = anyio.Event()

        # Check if should_exit got set while we set up the event
        if AppStatus.should_exit:
            return

        # Await the event
        await AppStatus.should_exit_event.wait()

    async def stream_response(self, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )
        async for data in self.body_iterator:
            chunk = ensure_bytes(data)
            _log.debug(f"chunk: {chunk.decode()}")
            await send({"type": "http.response.body", "body": chunk, "more_body": True})

        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def safe_send(message):
            async with self._send_lock:
                return await send(message)

        async with anyio.create_task_group() as task_group:
            # https://trio.readthedocs.io/en/latest/reference-core.html#custom-supervisors
            async def wrap(func: Callable[[], Coroutine[None, None, None]]) -> None:
                await func()
                # noinspection PyAsyncCall
                task_group.cancel_scope.cancel()

            task_group.start_soon(wrap, partial(self.stream_response, safe_send))
            task_group.start_soon(wrap, partial(self._ping, safe_send))
            task_group.start_soon(wrap, self.listen_for_exit_signal)

            if self.data_sender_callable:
                task_group.start_soon(self.data_sender_callable)

            await wrap(partial(self.listen_for_disconnect, receive))

        if self.background is not None:  # pragma: no cover, tested in StreamResponse
            await self.background()

    def enable_compression(self, force: bool = False) -> None:
        raise NotImplementedError

    @property
    def ping_interval(self) -> Union[int, float]:
        """Time interval between two ping massages"""
        return self._ping_interval

    @ping_interval.setter
    def ping_interval(self, value: Union[int, float]) -> None:
        """Setter for ping_interval property.

        :param int value: interval in sec between two ping values.
        """

        if not isinstance(value, (int, float)):
            raise TypeError("ping interval must be int")
        if value < 0:
            raise ValueError("ping interval must be greater then 0")

        self._ping_interval = value

    async def _ping(self, send: Send) -> None:
        # Legacy proxy servers are known to, in certain cases, drop HTTP connections after a short timeout.
        # To protect against such proxy servers, authors can send a custom (ping) event
        # every 15 seconds or so.
        # Alternatively one can send periodically a comment line
        # (one starting with a ':' character)
        while self.active:
            await anyio.sleep(self._ping_interval)
            if self.ping_message_factory:
                assert isinstance(self.ping_message_factory, Callable)  # type: ignore  # https://github.com/python/mypy/issues/6864
            ping = (
                ServerSentEvent(comment=f"ping - {datetime.utcnow()}").encode()
                if self.ping_message_factory is None
                else ensure_bytes(self.ping_message_factory())
            )
            _log.debug(f"ping: {ping.decode()}")
            await send({"type": "http.response.body", "body": ping, "more_body": True})
