from websockets.exceptions import WebSocketException


class FlowYamlParseException(Exception):
    """ Exception during loading yaml file for Flow creation"""


class FlowCreationException(Exception):
    """ Exception during flow creation via pods"""


class FlowBadInputException(Exception):
    """ Exception during loading Flow, no valid configuration"""


class FlowStartException(Exception):
    """ Exception during flow start"""


class PodStartException(Exception):
    """ Exception during pod start """


class PeaStartException(Exception):
    """ Exception during pod start """


class NoSuchFileException(WebSocketException):
    """ Exception during log streaming if no file is found """
