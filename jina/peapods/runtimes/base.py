import argparse

from ...logging import JinaLogger


class BaseRuntime:
    """A Jina Runtime is a procedure that blocks the main process once running (i.e. :meth:`run_forever`),
    therefore must be put into a separated thread/process. Any program/library/package/module that blocks the main
    process, can be formulated into a :class:`BaseRuntime` class and then be used in :class:`BasePea`.

     In the sequel, we call the main process/thread as ``M``, the process/thread blocked :class:`Runtime` as ``S``.

     In Jina, a :class:`BasePea` object is used to manage a :class:`Runtime` object's lifecycle. A :class:`BasePea`
     is a subclass of :class:`multiprocessing.Process` or :class:`threading.Thread`, it starts from ``M`` and once the
     ``S`` is spawned, it calls :class:`Runtime` methods in the following order:

        0. :meth:`__init__` in ``M``

        1. :meth:`setup` in ``S``

        2. :meth:`run_forever` in ``S``. Note that this will block ``S``, step 3 won't be
        reached until it is unblocked by :meth:`cancel`

        3. :meth:`teardown` in ``S``. Note that ``S`` is blocked by
        :meth:`run_forever`, this step won't be reached until step 2 is unblocked by :meth:`cancel`

     The :meth:`setup` and :meth:`teardown` pair together, which defines instructions that will be executed before
     and after. In subclasses, they are optional.

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
        :meth:`run_forever`, :meth:`cancel`, :meth:`setup`, :meth:`teardown`, then DO NOT catch exception in them.
        Exception is MUCH better handled by :class:`BasePea`.


     .. seealso::

        :class:`BasePea` for managing a :class:`Runtime` object's lifecycle.

    """

    def run_forever(self):
        """Running the blocking procedure inside ``S``. Note, once this method is called,
        ``S`` is blocked.

        .. note::

            If this method raises any exception, :meth:`teardown` will be called.

        .. seealso::

            :meth:`cancel` for cancelling the forever loop.
        """
        raise NotImplementedError

    def cancel(self):
        """Cancelling :meth:`run_forever` from ``M``. :meth:`cancel` usually requires some special communication
        between ``M`` and ``S``, e.g.

        - Use :class:`threading.Event` or `multiprocessing.Event`, while :meth:`run_forever` polls for this event
        - Use ZMQ to send a message, while :meth:`run_forever` polls for this message
        - Use HTTP/REST to send a request, while :meth:`run_forever` listens to this request

        .. seealso::

            :meth:`run_forever` for blocking the process/thread.
        """
        raise NotImplementedError

    def activate(self):
        """Send activate control message."""
        raise NotImplementedError

    def deactivate(self):
        """Send deactivate control message."""
        raise NotImplementedError

    def setup(self):
        """Method called to prepare the runtime inside ``S``. Optional in subclasses.
        The default implementation does nothing.

        .. note::

            If this method raises any exception, then :meth:`run_forever` and :meth:`teardown` won't be called.

        .. note::

            Unlike :meth:`__init__` called in ``M``, :meth:`setup` is called inside ``S``.
        """
        pass

    def teardown(self):
        """Method called immediately after :meth:`run_forever` is unblocked.
        You can tidy up things here.  Optional in subclasses. The default implementation does nothing.

        .. note::

            This method will only be called if the :meth:`setup` succeeds.
        """
        self.logger.close()

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__()
        self.args = args
        if args.name:
            self.name = f'{args.name}/{self.__class__.__name__}'
        else:
            self.name = self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(self.args))
