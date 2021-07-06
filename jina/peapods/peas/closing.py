from abc import abstractmethod
from typing import Optional, Union

from ..zmq import send_ctrl_message
from ...logging.logger import JinaLogger

if False:
    import multiprocessing
    import threading


class RuntimeClose:
    """
    :class:`RuntimeClose` is a class encapsulating the different types of closing routines used by Peas to close their matching `Runtimes`

    :param zed_runtime_ctrl: the runtime control address
    :param timeout_ctrl: the timeout control time for control port communication
    """

    def __init__(
        self,
        zed_runtime_ctrl_address: str,
        timeout_ctrl: int,
        logger: JinaLogger,
        *args,
        **kwargs,
    ):
        super().__init__()
        self._zed_runtime_ctrl_address = zed_runtime_ctrl_address
        self._timeout_ctrl = timeout_ctrl
        self.logger = logger

    @abstractmethod
    def cancel_runtime(self):
        """Implement logic to cancel the runtime"""
        ...


class SingletonRuntimeClose(RuntimeClose):
    """
    :class:`SingletonRuntimeClose` is a class encapsulating the logic to close a `SingleTonRuntime` (simply sending a TERMINATE signal)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.warning(f' Instantiating a `SingletonRuntimeClose`')

    def cancel_runtime(self):
        """Send terminate control message."""
        send_ctrl_message(
            self._zed_runtime_ctrl_address, 'TERMINATE', timeout=self._timeout_ctrl
        )


class DealerRuntimeClose(RuntimeClose):
    """
    :class:`DealerRuntimeClose` is a class encapsulating the logic to close a runtime of a `Dealer`.
    It sends a `TERMINATE_WORKER` signal to the router of the dealer with the `identity` of its `runtime` to guarantee
    a lock-free closure

    :param router_ctrl_address: if a dealer, a router control address is required for proper closing
    :param zmq_identity: the zmqlet identity of the ZedRuntime it wants to close
    """

    def __init__(self, router_ctrl_address: str, zmq_identity: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.warning(f' Instantiating a `DealerRuntimeClose`')
        self._router_ctrl_address = router_ctrl_address
        self._zmq_identity = zmq_identity

    def cancel_runtime(self):
        """Send terminate worker control message to the router."""
        # cancel should be sent with the right envelope and the address of `zed_runtime_ctrl`
        # TODO: This control address may need to be revisited as the address may differ with respect to the router
        parameters = {
            'dealer_ctrl_address': self._zed_runtime_ctrl_address,
            'dealer_identity': self._zmq_identity,
            'timeout_ctrl': self._timeout_ctrl,
        }
        send_ctrl_message(
            self._router_ctrl_address,
            'TERMINATE_WORKER',
            timeout=self._timeout_ctrl,
            parameters=parameters,
        )


class EventRuntimeClose(RuntimeClose):
    """
    :class:`EventRuntimeClose` is a class encapsulating the logic to close some runtimes based on events. Specially JinaD and AsyncGateway Runtimes

    JinaD runtime will actually implement a proper `DealerRuntimeClose` or `SingletonRuntimeClose` on their remote.

    :param cancel_event: the multiprocessing event communication needed to close specific runtimes
    """

    def __init__(
        self,
        cancel_event: Union['multiprocessing.Event', 'threading.Event'],
        logger: JinaLogger,
        *args,
        **kwargs,
    ):
        logger.warning(f' Instantiating a `EventRuntimeClose`')
        self._cancel_event = cancel_event

    def cancel_runtime(self):
        """Set the cancel event"""
        self._cancel_event.set()


class RuntimeCloseFactory:
    """
    :class:`RuntimeCloseFactory` is a factory method to create `RuntimeClose` instances.
    """

    @staticmethod
    def build_runtime_close(
        is_dealer: bool,
        zed_runtime_ctrl: str,
        timeout_ctrl: int,
        cancel_event: Union['multiprocessing.Event', 'threading.Event'],
        zmq_identity: Optional[str],
        router_ctrl_address: Optional[str],
        runtime_cls,
        logger: JinaLogger,
    ) -> RuntimeClose:
        """Build an implementation of a `BasePod` interface

        :param is_dealer: flag indicating if the runtime to close is from a dealer Pea
        :param zed_runtime_ctrl: the runtime control address
        :param timeout_ctrl: the timeout control time for control port communication
        :param cancel_event: the multiprocessing event communication needed to close specific runtimes
        :param zmq_identity: the zmqlet identity of the ZedRuntime it wants to close
        :param router_ctrl_address: if a dealer, a router control address is required for proper closing
        :param runtime_cls: The type of runtime class to close
        :param logger: The logger of the closing from the Pea
        :return: the created BasePod
        """
        from ..runtimes.zmq.zed import ZEDRuntime
        from ..runtimes.container import ContainerRuntime

        if runtime_cls != ZEDRuntime and runtime_cls != ContainerRuntime:
            return EventRuntimeClose(cancel_event=cancel_event, logger=logger)
        elif is_dealer:
            if not router_ctrl_address:
                raise AssertionError(
                    'To properly close a `dealer\'s` pea runtime, it needs to know its router control address'
                )
            return DealerRuntimeClose(
                router_ctrl_address=router_ctrl_address,
                zed_runtime_ctrl_address=zed_runtime_ctrl,
                timeout_ctrl=timeout_ctrl,
                zmq_identity=zmq_identity,
                logger=logger,
            )
        else:
            return SingletonRuntimeClose(
                zed_runtime_ctrl_address=zed_runtime_ctrl,
                timeout_ctrl=timeout_ctrl,
                logger=logger,
            )
