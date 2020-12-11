from typing import Dict, Set

from . import BasePod, PodRoleType
from .flow import FlowPod
from ..peas.gateway.grpc import GatewayPea
from ..peas.gateway.rest import RESTGatewayPea
from ...parser import set_gateway_parser


class GatewayPod(BasePod):
    """A :class:`BasePod` that holds a Gateway """

    def start(self) -> 'GatewayPod':
        for s in self.all_args:
            p = RESTGatewayPea(s) if getattr(s, 'rest_api', False) else GatewayPea(s)
            self.peas.append(p)
            self.enter_context(p)

        self.start_sentinels()
        return self


class GatewayFlowPod(GatewayPod, FlowPod):
    """A :class:`FlowPod` that holds a Gateway """

    def __init__(self, kwargs: Dict = None, needs: Set[str] = None):
        FlowPod.__init__(self, kwargs, needs, parser=set_gateway_parser)
        self.role = PodRoleType.GATEWAY
