from typing import Dict, Set

from . import BasePod, PodRoleType
from .flow import FlowPod
from ..runtimes.local import LocalRuntime
from ..peas.gateway import GatewayPea, RESTGatewayPea
from ...parser import set_gateway_parser


class GatewayPod(BasePod):
    """A :class:`BasePod` that holds a Gateway """

    def start(self) -> 'GatewayPod':
        for s in self.all_args:
            pea_cls = RESTGatewayPea if getattr(s, 'rest_api', False) else GatewayPea
            r = LocalRuntime(s, pea_cls=pea_cls)
            self.runtimes.append(r)
            self.enter_context(r)

        self.start_sentinels()
        return self


class GatewayFlowPod(GatewayPod, FlowPod):
    """A :class:`FlowPod` that holds a Gateway """

    def __init__(self, kwargs: Dict = None, needs: Set[str] = None):
        FlowPod.__init__(self, kwargs, needs, parser=set_gateway_parser)
        self.role = PodRoleType.GATEWAY
