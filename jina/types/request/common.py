from . import Request
from ...proto import jina_pb2


class DryRunRequest(Request):
    """Base empty request for dry run"""


class TrainDryRunRequest(DryRunRequest):
    """Empty train request for dry run"""

    def __init__(self):
        super().__init__()
        self.as_pb_object.train.CopyFrom(jina_pb2.RequestProto.TrainRequestProto())


class IndexDryRunRequest(DryRunRequest):
    """Empty index request for dry run"""

    def __init__(self):
        super().__init__()
        self.as_pb_object.index.CopyFrom(jina_pb2.RequestProto.IndexRequestProto())


class SearchDryRunRequest(DryRunRequest):
    """Empty search request for dry run"""

    def __init__(self):
        super().__init__()
        self.as_pb_object.search.CopyFrom(jina_pb2.RequestProto.SearchRequestProto())


class ControlDryRunRequest(DryRunRequest):
    """Empty control request for dry run"""

    def __init__(self):
        super().__init__()
        self.as_pb_object.control.CopyFrom(jina_pb2.RequestProto.ControlRequestProto())
