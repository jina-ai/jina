import argparse
from typing import Union

from ...excepts import RuntimeTerminated
from ...logging.logger import JinaLogger

if False:
    import multiprocessing
    import threading


class BaseRuntime:
    """A Jina Runtime is a procedure that blocks the main process once running (i.e. :meth:`run_forever`),
    therefore must be put into a separated thread/process. Any program/library/package/module that blocks the main
    process, can be formulated into a :class:`BaseRuntime` class and then be used in :class:`BasePea`.

     In the sequel, we call the main process/thread as ``M``, the process/thread blocked :class:`Runtime` as ``S``.

     In Jina, a :class:`BasePea` object is used to manage a :class:`Runtime` object's lifecycle. A :class:`BasePea`
     acts as a :class:`multiprocessing.Process` or :class:`threading.Thread`, it starts from ``M`` and once the
     ``S`` is spawned, it calls :class:`Runtime` methods in the following order:

        0. :meth:`__init__`

        1. :meth:`run_forever`. Note that this will block ``S``, step 3 won't be
        reached until it is unblocked by :meth:`cancel`. This method is responsible
        to set the `ready_event` to guarantee that the rest of the system knows when it is ready
        to receive messages.

        2. :meth:`teardown` in ``S``. Note that ``S`` is blocked by
        :meth:`run_forever`, this step won't be reached until step 2 is unblocked by :meth:`cancel`

     The :meth:`__init__` and :meth:`teardown` pair together, which defines instructions that will be executed before
     and after. In subclasses, `teardown` is optional.

     The :meth:`run_forever` and :meth:`cancel` pair together, which introduces blocking to ``S`` and then
     unblocking from it. They are mandatory for all subclasses.

     Note that, there is no "exclusive" relation between :meth:`run_forever` and :meth:`teardown`, :meth:`teardown`
     is not about "cancelling", it is about "cleaning".

     Unlike other three methods that get invoked inside ``S``, the :meth:`cancel` is invoked in ``M`` to unblock ``S``.
     Therefore, :meth:`cancel` usually requires some special communication between ``M`` and ``S``, e.g.

        - Use :class:`threading.Event` or `multiprocessing.Event`, while :meth:`run_forever` polls for this event
        - Use ZMQ to send a message, while :meth:`run_forever` polls for this message
        - Use HTTP/REST to send a request, while :meth:`run_forever` listens to this request

     Note, another way to jump out from :meth:`run_forever` is raise exceptions from it. This will immediately move to
     :meth:`teardown`.

     .. note::
        Rule of thumb on exception handling: if you are not sure if you should handle exception inside
        :meth:`run_forever`, :meth:`cancel`, :meth:`teardown`, then DO NOT catch exception in them.
        Exception is MUCH better handled by :class:`BasePea`.


     .. seealso::

        :class:`BasePea` for managing a :class:`Runtime` object's lifecycle.
    """

    def __init__(
        self,
        args: 'argparse.Namespace',
        ready_event: Union['multiprocessing.Event', 'threading.Event'],
        **kwargs,
    ):
        super().__init__()
        self.args = args
        if args.name:
            self.name = f'{args.name}/{self.__class__.__name__}'
        else:
            self.name = self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(self.args))
        self.is_ready_event = ready_event

    def run_forever(self):
        """Running the blocking procedure inside ``S``. Note, once this method is called,
        ``S`` is blocked.

        .. note::

            If this method raises any exception, :meth:`teardown` will be called.

        .. seealso::

            :meth:`cancel` for cancelling the forever loop.
        """
        raise NotImplementedError

    def teardown(self):
        """Method called immediately after :meth:`run_forever` is unblocked.
        You can tidy up things here.  Optional in subclasses. The default implementation does nothing.
        """
        self.logger.close()
        self.is_ready_event.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == RuntimeTerminated:
            self.logger.debug(f'{self!r} is ended')
        elif exc_type == KeyboardInterrupt:
            self.logger.debug(f'{self!r} is interrupted by user')
        elif exc_type in {Exception, SystemError}:
            self.logger.error(
                f'{exc_val!r} during {self.run_forever!r}'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
        try:
            self.teardown()
        except OSError:
            # OSError(Stream is closed) already
            pass
        except Exception as ex:
            self.logger.error(
                f'{ex!r} during {self.teardown!r}'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )

        # https://stackoverflow.com/a/28158006
        # return True will silent all exception stack trace here, silence is desired here as otherwise it is too
        # noisy
        #
        # doc: If an exception is supplied, and the method wishes to suppress the exception (i.e., prevent it
        # from being propagated), it should return a true value. Otherwise, the exception will be processed normally
        # upon exit from this method.
        return True
