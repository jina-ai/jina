""" This modules defines all kinds of exceptions raised in jina """


class MismatchedVersion(Exception):
    """When the jina version info of the incoming message does not match the local jina version"""


class WaitPendingMessage(Exception):
    """Waiting until all partial messages are received"""


class ExecutorFailToLoad(Exception):
    """When the executor can not be loaded in pea/pod"""


class MemoryOverHighWatermark(Exception):
    """When the memory usage is over the defined high water mark"""


class UnknownControlCommand(Exception):
    """The control command received can not be recognized"""


class EventLoopEnd(Exception):
    """The event loop of Pea ends"""


class DriverNotInstalled(Exception):
    """Driver is not installed in the Pea"""


class BadDriverGroup(Exception):
    """Driver group can not be found in the map"""


class BadDriverMap(Exception):
    """The YAML driver map is in a bad format"""


class NoRequestHandler(Exception):
    """No matched handler for this request """


class FlowTopologyError(Exception):
    """Flow exception when the topology is ambiguous."""


class FlowMissingPodError(Exception):
    """Flow exception when a pod can not be found in the flow."""


class FlowBuildLevelError(Exception):
    """Flow exception when required build level is higher than the current build level."""


class EmptyExecutorYAML(Exception):
    """The yaml config file is empty, nothing to read from there."""


class BadWorkspace(Exception):
    """Can not determine the separate storage strategy for the executor"""


class BadClient(Exception):
    """A wrongly defined grpc client, can not communicate with jina server correctly """


class BadPersistantFile(Exception):
    """Bad or broken dump file that can not be deserialized with ``pickle.load``"""
