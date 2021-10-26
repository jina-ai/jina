"""
BSD 2-Clause License

Copyright (c) 2018-2020, Ewald de Wit
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import asyncio
import asyncio.events as events
import os
import sys
import threading
from contextlib import contextmanager
from heapq import heappop


def apply(loop=None):
    """Patch asyncio to make its event loop reentrant."""
    loop = loop or asyncio.get_event_loop()
    if not isinstance(loop, asyncio.BaseEventLoop):
        raise ValueError('Can\'t patch loop of type %s' % type(loop))
    if getattr(loop, '_nest_patched', None):
        # already patched
        return
    _patch_asyncio()
    _patch_loop(loop)
    _patch_task()
    _patch_tornado()


def _patch_asyncio():
    """
    Patch asyncio module to use pure Python tasks and futures,
    use module level _current_tasks, all_tasks and patch run method.
    """

    def run(future, *, debug=False):
        loop = asyncio.get_event_loop()
        loop.set_debug(debug)
        return loop.run_until_complete(future)

    if sys.version_info >= (3, 6, 0):
        asyncio.Task = asyncio.tasks._CTask = asyncio.tasks.Task = asyncio.tasks._PyTask
        asyncio.Future = (
            asyncio.futures._CFuture
        ) = asyncio.futures.Future = asyncio.futures._PyFuture
    if sys.version_info < (3, 7, 0):
        asyncio.tasks._current_tasks = asyncio.tasks.Task._current_tasks  # noqa
        asyncio.all_tasks = asyncio.tasks.Task.all_tasks  # noqa
    if not hasattr(asyncio, '_run_orig'):
        asyncio._run_orig = getattr(asyncio, 'run', None)
        asyncio.run = run


def _patch_loop(loop):
    """Patch loop to make it reentrant."""

    def run_forever(self):
        with manage_run(self), manage_asyncgens(self):
            while True:
                self._run_once()
                if self._stopping:
                    break
        self._stopping = False

    def run_until_complete(self, future):
        with manage_run(self):
            f = asyncio.ensure_future(future, loop=self)
            if f is not future:
                f._log_destroy_pending = False
            while not f.done():
                self._run_once()
                if self._stopping:
                    break
            if not f.done():
                raise RuntimeError('Event loop stopped before Future completed.')
            return f.result()

    def _run_once(self):
        """
        Simplified re-implementation of asyncio's _run_once that
        runs handles as they become ready.
        """
        now = self.time()
        ready = self._ready
        scheduled = self._scheduled
        while scheduled and scheduled[0]._cancelled:
            heappop(scheduled)

        timeout = (
            0
            if ready or self._stopping
            else min(max(scheduled[0]._when - now, 0), 86400)
            if scheduled
            else None
        )
        event_list = self._selector.select(timeout)
        self._process_events(event_list)

        end_time = self.time() + self._clock_resolution
        while scheduled and scheduled[0]._when < end_time:
            handle = heappop(scheduled)
            ready.append(handle)

        for _ in range(len(ready)):
            if not ready:
                break
            handle = ready.popleft()
            if not handle._cancelled:
                handle._run()
        handle = None

    @contextmanager
    def manage_run(self):
        """Set up the loop for running."""
        self._check_closed()
        old_thread_id = self._thread_id
        old_running_loop = events._get_running_loop()
        try:
            self._thread_id = threading.get_ident()
            events._set_running_loop(self)
            self._num_runs_pending += 1
            if self._is_proactorloop:
                if self._self_reading_future is None:
                    self.call_soon(self._loop_self_reading)
            yield
        finally:
            self._thread_id = old_thread_id
            events._set_running_loop(old_running_loop)
            self._num_runs_pending -= 1
            if self._is_proactorloop:
                if (
                    self._num_runs_pending == 0
                    and self._self_reading_future is not None
                ):
                    ov = self._self_reading_future._ov
                    self._self_reading_future.cancel()
                    if ov is not None:
                        self._proactor._unregister(ov)
                    self._self_reading_future = None

    @contextmanager
    def manage_asyncgens(self):
        old_agen_hooks = sys.get_asyncgen_hooks()
        try:
            self._set_coroutine_origin_tracking(self._debug)
            if self._asyncgens is not None:
                sys.set_asyncgen_hooks(
                    firstiter=self._asyncgen_firstiter_hook,
                    finalizer=self._asyncgen_finalizer_hook,
                )
            yield
        finally:
            self._set_coroutine_origin_tracking(False)
            if self._asyncgens is not None:
                sys.set_asyncgen_hooks(*old_agen_hooks)

    def _check_running(self):
        """Do not throw exception if loop is already running."""
        pass

    cls = loop.__class__
    cls.run_forever = run_forever
    cls.run_until_complete = run_until_complete
    cls._run_once = _run_once
    cls._check_running = _check_running
    cls._check_runnung = _check_running  # typo in Python 3.7 source
    cls._nest_patched = True
    cls._num_runs_pending = 0
    cls._is_proactorloop = os.name == 'nt' and issubclass(
        cls, asyncio.ProactorEventLoop
    )
    if sys.version_info < (3, 7, 0):
        cls._set_coroutine_origin_tracking = cls._set_coroutine_wrapper


def _patch_task():
    """Patch the Task's step and enter/leave methods to make it reentrant."""

    def step(task, exc=None):
        curr_task = curr_tasks.get(task._loop)
        try:
            step_orig(task, exc)
        finally:
            if curr_task is None:
                curr_tasks.pop(task._loop, None)
            else:
                curr_tasks[task._loop] = curr_task

    Task = asyncio.Task
    if sys.version_info >= (3, 7, 0):

        def enter_task(loop, task):
            curr_tasks[loop] = task

        def leave_task(loop, task):
            curr_tasks.pop(loop, None)

        asyncio.tasks._enter_task = enter_task
        asyncio.tasks._leave_task = leave_task
        curr_tasks = asyncio.tasks._current_tasks
        step_orig = Task._Task__step
        Task._Task__step = step
    else:
        curr_tasks = Task._current_tasks
        step_orig = Task._step
        Task._step = step


def _patch_tornado():
    """
    If tornado is imported before nest_asyncio, make tornado aware of
    the pure-Python asyncio Future.
    """
    if 'tornado' in sys.modules:
        import tornado.concurrent as tc

        tc.Future = asyncio.Future
        if asyncio.Future not in tc.FUTURES:
            tc.FUTURES += (asyncio.Future,)
