from .. import Pod
from ...types.routing.graph import RoutingGraph


class GatewayPod(Pod):
    """A GatewayPod is a context manager for the gateway pea.

    :param args: pod arguments parsed from the CLI. These arguments will be used for each of the replicas
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    def set_routing_graph(self, routing_graph: RoutingGraph):
        """Sets the routing graph for the Gateway. The Gateway will equip each message with the given graph.

        :param routing_graph: The to-be-used routing graph
        """
        self.args.routing_graph = routing_graph
