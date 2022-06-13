"""This modules defines all kinds of exceptions raised in Jina."""
from typing import Set, Union

import grpc.aio


class BaseJinaException(BaseException):
    """A base class for all exceptions raised by Jina"""


class RuntimeFailToStart(SystemError, BaseJinaException):
    """When pod/deployment is failed to started."""


class RuntimeTerminated(KeyboardInterrupt, BaseJinaException):
    """The event loop of BasePod ends."""


class FlowTopologyError(Exception, BaseJinaException):
    """Flow exception when the topology is ambiguous."""


class FlowMissingDeploymentError(Exception, BaseJinaException):
    """Flow exception when a deployment can not be found in the flow."""


class FlowBuildLevelError(Exception, BaseJinaException):
    """Flow exception when required build level is higher than the current build level."""


class BadConfigSource(FileNotFoundError, BaseJinaException):
    """The yaml config file is bad, not loadable or not exist."""


class BadClient(Exception, BaseJinaException):
    """A wrongly defined client, can not communicate with jina server correctly."""


class BadClientCallback(BadClient, BaseJinaException):
    """Error in the callback function on the client side."""


class BadClientInput(BadClient, BaseJinaException):
    """Error in the request generator function on the client side."""


class BadRequestType(TypeError, BaseJinaException):
    """Exception when can not construct a request object from given data."""


class BadImageNameError(Exception, BaseJinaException):
    """Exception when an image name can not be found either local & remote"""


class BadYAMLVersion(Exception, BaseJinaException):
    """Exception when YAML config specifies a wrong version number."""


class NotSupportedError(Exception, BaseJinaException):
    """Exception when user accidentally using a retired argument."""


class RuntimeRunForeverEarlyError(Exception, BaseJinaException):
    """Raised when an error occurs when starting the run_forever of Runtime"""


class DockerVersionError(SystemError, BaseJinaException):
    """Raised when the docker version is incompatible"""


class NoContainerizedError(Exception, BaseJinaException):
    """Raised when trying to use non-containerized Executor in K8s or Docker Compose"""


class PortAlreadyUsed(RuntimeError, BaseJinaException):
    """Raised when to use a port which is already used"""


class InternalNetworkError(grpc.aio.AioRpcError, BaseJinaException):
    """
    Raised when communication between microservices fails.
    Needed to propagate information about the root cause event, such as request_id and dest_addr.
    """

    def __init__(
        self,
        og_exception: grpc.aio.AioRpcError,
        request_id: str = '',
        dest_addr: Union[str, Set[str]] = {''},
        details: str = '',
    ):
        """
        :param og_exception: the original exception that caused the network error
        :param request_id: id of the request that caused the error
        :param dest_addr: destination (microservice) address(es) of the problematic network call(s)
        :param details: details of the error
        """
        self.og_exception = og_exception
        self.request_id = request_id
        self.dest_addr = dest_addr
        self._details = details
        super().__init__(
            og_exception.code(),
            og_exception.initial_metadata(),
            og_exception.trailing_metadata(),
            self.details(),
            og_exception.debug_error_string(),
        )

    def __str__(self):
        return self.details()

    def __repr__(self):
        return self.__str__()

    def code(self):
        """
        :return: error code of this exception
        """
        return self.og_exception.code()

    def details(self):
        """
        :return: details of this exception
        """
        return self._details if self._details else self.og_exception.details()
