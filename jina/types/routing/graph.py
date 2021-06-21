from typing import List

from collections import defaultdict

from ...proto import jina_pb2


class TargetPod:
    """
    Wrapper class around `TargetPodProto`.

    It offers a Pythonic interface to allow users access to the
    :class:`jina.jina_pb2.TargetPodProto` object without working with Protobuf itself.

    :param target: the protobuff object of the TargetPod
    """

    def __init__(self, target: 'jina_pb2.TargetPodProto') -> None:
        self.proto = target

    @property
    def port(self) -> int:
        """Returns the `port` field of this TargetPod

        :return: port
        """
        return self.proto.port

    @property
    def host(self) -> str:
        """Returns the `host` field of this TargetPod

        :return: host
        """
        return self.proto.host

    @property
    def full_address(self) -> str:
        """Return the full zmq adress of this TargetPod

        :return: address
        """
        return f'{self.host}:{self.port}'

    @property
    def expected_parts(self) -> int:
        """Return the `expected_parts` field of this TargetPod

        :return: expected_parts
        """
        return self.proto.expected_parts

    @expected_parts.setter
    def expected_parts(self, value: int) -> None:
        """Sets the number of expected incoming message for a Pod.

        :param value: the new number of expected parts
        """
        self.proto.expected_parts = value

    @property
    def out_edges(self) -> List[str]:
        """Return the `out_edges` field of this TargetPod

        :return: out_edges
        """
        return list(self.proto.out_edges)

    def add_edge(self, to_pod: str) -> None:
        """Adds an edge to the internal representation of the out_edges.

        :param to_pod: the name of the pod outtraffic should go to
        """
        self.proto.out_edges.append(to_pod)


class RoutingGraph:
    """
    Wrapper class around `RoutingGraphProto`.

    It offers a Pythonic interface to allow users access to the
    :class:`jina.jina_pb2.RoutingGraphProto` object without working with Protobuf itself.

    :param graph: the protobuff object of the RoutingGraph
    """

    def __init__(self, graph: 'jina_pb2.RoutingGraphProto' = None) -> None:
        if graph is None:
            graph = jina_pb2.RoutingGraphProto()
        self.proto = graph

    def add_edge(self, from_pod: str, to_pod: str) -> None:
        """Adds an edge to the graph.

        :param from_pod: Pod from which traffic is send
        :param to_pod: Pod to which traffic is send
        """
        self._get_target_pod(from_pod).add_edge(to_pod)
        self._get_target_pod(to_pod).expected_parts += 1

    def add_pod(self, pod_name: str, host: str, port: int) -> None:
        """Adds a Pod vertex to the graph.

        :param pod_name: the name of the Pod. Should be unique to the graph.
        :param host: the host of the Pod.
        :param port: the port of the Pod.
        """
        if pod_name in self.pods:
            raise ValueError(
                f'Vertex with name {pod_name} already exists. Please check your configuration for unique Pod names.'
            )
        target = self.pods[pod_name]
        target.host = host
        target.port = port

    def _get_target_pod(self, pod: str) -> TargetPod:
        return TargetPod(self.pods[pod])

    @property
    def active_pod(self) -> str:
        """
        :return: the active Pod name
        """
        return self.proto.active_pod

    @active_pod.setter
    def active_pod(self, pod_name: str) -> None:
        """Sets the currently active Pod in the routing.

        .. # noqa: DAR101
        """
        self.proto.active_pod = pod_name

    def _get_out_edges(self, pod: str) -> List[str]:
        return self._get_target_pod(pod).out_edges

    @property
    def active_target_pod(self) -> TargetPod:
        """
        :return: a :class:`TargetPod` object of the currently active Pod
        """
        return TargetPod(self.pods[self.active_pod])

    @property
    def pods(self):
        """
        :return: all Pod/vertices of the graph.
        """
        return self.proto.pods

    def get_next_targets(self) -> List['RoutingGraph']:
        """
        Calculates next routing graph for all currently outgoing edges.

        :return: new routing graphs with updated active Pods.
        """
        targets = []
        for next_pod_index in self._get_out_edges(self.active_pod):
            new_graph = jina_pb2.RoutingGraphProto()
            new_graph.CopyFrom(self.proto)
            new_graph.active_pod = next_pod_index
            targets.append(RoutingGraph(new_graph))
        return targets

    def is_acyclic(self) -> bool:
        """
        :return: True, if graph is acyclic, False otherwise.
        """
        topological_sorting = self._topological_sort()
        position_lookup = {
            pod: position for position, pod in enumerate(topological_sorting)
        }

        for first in topological_sorting:
            for second in self._get_out_edges(first):

                if position_lookup[first] > position_lookup[second]:

                    return False
        return True

    def _topological_sort(self):
        """
        Calculates a topological sorting. It uses internally _topological_sort_pod()
        For more information see https://en.wikipedia.org/wiki/Topological_sorting

        :return: topological sorting of all Pods by podname
        """

        visited = defaultdict(bool)
        stack = []

        for pod in self.pods:
            if not visited[pod]:
                self._topological_sort_pod(pod, visited, stack)

        return stack[::-1]

    def _topological_sort_pod(self, pod, visited, stack):
        visited[pod] = True

        for out_pod in self._get_out_edges(pod):
            if not visited[out_pod]:
                self._topological_sort_pod(out_pod, visited, stack)

        stack.append(pod)
