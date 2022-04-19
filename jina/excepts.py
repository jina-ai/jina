"""This modules defines all kinds of exceptions raised in Jina."""
from jina.helper import deprecated_method


class BaseJinaException(BaseException):
    """A base class for all exceptions raised by Jina"""


@deprecated_method('BaseJinaException')
class BaseJinaExeception(BaseException):
    """A base class for all exceptions raised by Jina"""


class ExecutorFailToLoad(SystemError, BaseJinaException):
    """When the executor can not be loaded in pod/deployment."""


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


class BadClientResponse(Exception, BaseJinaException):
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
