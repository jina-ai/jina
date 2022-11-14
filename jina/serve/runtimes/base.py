import argparse

from jina.excepts import RuntimeTerminated
from jina.logging.logger import JinaLogger


class BaseRuntime:
    """
    A Jina Runtime is a procedure that blocks the main process once running (i.e. :meth:`run_forever`),
    therefore should be put into a separated thread/process, or inside the main process of a docker container.
    Any program/library/package/module that blocks the main process, can be formulated into a :class:`BaseRuntime` class
    and then be started from a :class:`Pod`.

    In the sequel, we call the main process/thread as ``M``, the process/thread blocked :class:`Runtime` as ``S``.

    In Jina, a :class:`Pod` object is used to manage a :class:`Runtime` object's lifecycle. A :class:`Pod`
    acts as a :class:`multiprocessing.Process` or :class:`threading.Thread`, it starts from ``M`` and once the
    ``S`` is spawned, it uses :class:`Runtime` as a context manager:

        0. :meth:`__init__`

        1. :meth: `__enter__`

        2. :meth:`run_forever`. Note that this will block ``S``, step 3 won't be
        reached until it is unblocked by :meth:`cancel`.

        3. When an error occurs during `run_forever` or `cancel` signal is reached by the `runtime`. The `run_forever` method is cancelled and
        the managed context is closed. The `__exit__` of `Runtime` guarantees that the `Runtime` is properly shut by calling `teardown`.

    The :meth:`__init__` and :meth:`teardown` pair together, which defines instructions that will be executed before
    and after. In subclasses, `teardown` is optional.

    In order to cancel the `run_forever` method of a `Runtime`, you can use their `static` `cancel` method that will make sure that the runtime is properly cancelled.

    - Use :class:`threading.Event` or `multiprocessing.Event`, while :meth:`run_forever` polls for this event
    - Use :class:`GrpcConnectionPool` to send a TERMINATE message, while :meth:`run_forever` polls for this message

    Note, another way to jump out from :meth:`run_forever` is raise exceptions from it. This will immediately move to
    :meth:`teardown`.

     .. note::
        Rule of thumb on exception handling: if you are not sure if you should handle exception inside
        :meth:`run_forever`, :meth:`cancel`, :meth:`teardown`, then DO NOT catch exception in them.
        Exception is MUCH better handled by :class:`Pod`.


     .. seealso::

        :class:`Pod` for managing a :class:`Runtime` object's lifecycle.
    """

    def __init__(
        self,
        args: 'argparse.Namespace',
        **kwargs,
    ):
        super().__init__()
        self.args = args
        if args.name:
            self.name = f'{args.name}/{self.__class__.__name__}'
        else:
            self.name = self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(self.args))

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == RuntimeTerminated:
            self.logger.debug(f'{self!r} is ended')
        elif exc_type == KeyboardInterrupt:
            self.logger.debug(f'{self!r} is interrupted by user')
        elif exc_type and issubclass(exc_type, Exception):
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
