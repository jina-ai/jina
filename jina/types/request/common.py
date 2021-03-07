from . import Request
from ...proto import jina_pb2

__all__ = [
    'TrainDryRunRequest',
    'IndexDryRunRequest',
    'SearchDryRunRequest',
    'ControlDryRunRequest',
    'DryRunRequest',
]


class DryRunRequest(Request):
    """Base empty request for dry run."""


class TrainDryRunRequest(DryRunRequest):
    """Empty train request for dry run."""

    def __init__(self):
        """Set the constructor."""
        super().__init__()
        self.proto.train.CopyFrom(jina_pb2.RequestProto.TrainRequestProto())


class IndexDryRunRequest(DryRunRequest):
    """Empty index request for dry run."""

    def __init__(self):
        """Set the constructor."""
        super().__init__()
        self.proto.index.CopyFrom(jina_pb2.RequestProto.IndexRequestProto())


class SearchDryRunRequest(DryRunRequest):
    """Empty search request for dry run."""

    def __init__(self):
        """Set the constructor."""
        super().__init__()
        self.proto.search.CopyFrom(jina_pb2.RequestProto.SearchRequestProto())


class ControlDryRunRequest(DryRunRequest):
    """Empty control request for dry run."""

    def __init__(self):
        """Set the constructor."""
        super().__init__()
        self.proto.control.CopyFrom(jina_pb2.RequestProto.ControlRequestProto())
