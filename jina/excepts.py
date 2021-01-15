""" This modules defines all kinds of exceptions raised in jina """

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


class NoExplicitMessage(Exception):
    """Waiting until all partial messages are received"""


class ChainedPodException(Exception):
    """Chained exception from the last Pod"""


class MismatchedVersion(SystemError):
    """When the jina version info of the incoming message does not match the local jina version"""


class ExecutorFailToLoad(SystemError):
    """When the executor can not be loaded in pea/pod"""


class RuntimeFailToStart(SystemError):
    """When pea/pod is failed to started"""


class MemoryOverHighWatermark(Exception):
    """When the memory usage is over the defined high water mark"""


class DriverError(Exception):
    """Driver related exceptions"""


class RuntimeTerminated(KeyboardInterrupt):
    """The event loop of BasePea ends"""


class PodRunTimeError(Exception):
    """The error propagated by Pods when Executor throws an exception"""


class DriverNotInstalled(DriverError):
    """Driver is not installed in the BasePea"""


class NoDriverForRequest(DriverError):
    """No matched driver for this request """


class UnattachedDriver(DriverError):
    """Driver is not attached to any BasePea or executor"""


class UnknownControlCommand(RuntimeError):
    """The control command received can not be recognized"""


class FlowTopologyError(Exception):
    """Flow exception when the topology is ambiguous."""


class FlowConnectivityError(Exception):
    """Flow exception when the flow is not connective via network."""


class FlowMissingPodError(Exception):
    """Flow exception when a pod can not be found in the flow."""


class FlowBuildLevelError(Exception):
    """Flow exception when required build level is higher than the current build level."""


class EmptyExecutorYAML(Exception):
    """The yaml config file is empty, nothing to read from there."""


class BadConfigSource(FileNotFoundError):
    """The yaml config file is bad, not loadable or not exist"""


class BadWorkspace(Exception):
    """Can not determine the separate storage strategy for the executor"""


class BadClient(Exception):
    """A wrongly defined grpc client, can not communicate with jina server correctly """


class BadClientCallback(BadClient):
    """Error in the callback function on the client side"""


class BadClientInput(BadClient):
    """Error in the request generator function on the client side"""


class BadPersistantFile(Exception):
    """Bad or broken dump file that can not be deserialized with ``pickle.load``"""


class GRPCServerError(Exception):
    """Can not connect to the grpc gateway"""


class GatewayPartialMessage(Exception):
    """Gateway receives a multi-part message but it can not handle it"""


class UndefinedModel(Exception):
    """Any time a non-defined model is tried to be used """


class MongoDBException(Exception):
    """ Any errors raised by MongoDb """


class TimedOutException(Exception):
    """ Errors raised for timeout operations """


class DockerLoginFailed(Exception):
    """ Exception to raise for docker hub login failures """


class ModelCheckpointNotExist(FileNotFoundError):
    """ Exception to raise for executors depending on pretrained model files when they do not exist """


class PretrainedModelFileDoesNotExist(ModelCheckpointNotExist):
    """ Depreciated, used in the hub executors

    TODO: to be removed after hub executors uses ModelCheckpointNotExist
    """


class HubBuilderError(Exception):
    """ Base exception to raise when :command:`jina hub build` fails"""


class HubBuilderBuildError(HubBuilderError):
    """ Exception to raise when :command:`jina hub build` fails to build image"""


class HubBuilderTestError(HubBuilderError):
    """ Exception to raise when :command:`jina hub build` fails to test image"""


class CompressionRateTooLow(Exception):
    """ Compression rate is too low, no need to compression"""


class DryRunException(Exception):
    """Dryrun is not successful on the given flow"""


class BadDocID(Exception):
    """ Exception when user give a non-hex string as the doc id """


class BadDocType(TypeError):
    """ Exception when can not construct a document from the given data """


class BadQueryLangType(TypeError):
    """ Exception when can not construct a query language from the given data """


class BadRequestType(TypeError):
    """Exception when can not construct a request object from given data"""


class BadNamedScoreType(TypeError):
    """ Exception when can not construct a named score from the given data """


class LengthMismatchException(Exception):
    """ Exception when length of two items should be identical while not """


class ImageAlreadyExists(Exception):
    """ Exception when an image with the name, module version, and Jina version already exists on the Hub"""


class BadFlowYAMLVersion(Exception):
    """ Exception when Flow YAML config specifies a wrong version number"""


class LookupyError(Exception):
    """Base exception class for all exceptions raised by lookupy"""


class EventLoopError(Exception):
    """ Exception when a running event loop is found but not under jupyter or ipython """


class ZMQSocketError(Exception):
    """Exeception when ZMQlet/ZMQStreamlet can not be initialized """


class HubLoginRequired(Exception):
    """ Exception to raise for jina hub login """


class DaemonConnectivityError(Exception):
    """ Exception to raise when jina daemon is not connectable"""
