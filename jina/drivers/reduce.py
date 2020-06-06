__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from collections import defaultdict
from typing import Dict, List

from .control import ControlReqDriver
from ..excepts import NoExplicitMessage
from ..proto import is_data_request, jina_pb2


class BaseReduceDriver(ControlReqDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prev_requests = None
        self._prev_messages = None
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List]

    @property
    def prev_reqs(self) -> List['jina_pb2.Request']:
        """Get all previous requests that has the same ``request_id``, shortcut to ``self.pea.prev_requests``

        This returns ``None`` when ``num_part=1``.
        """
        return self._prev_requests

    @property
    def prev_msgs(self) -> List['jina_pb2.Message']:
        """Get all previous messages that has the same ``request_id``, shortcut to ``self.pea.prev_messages``

        This returns ``None`` when ``num_part=1``.
        """
        return self._prev_messages

    def __call__(self, *args, **kwargs):
        if is_data_request(self.req):
            if self.envelope.num_part[-1] > 1:
                req_id = self.envelope.request_id
                self._pending_msgs[req_id].append(self.msg)
                num_req = len(self._pending_msgs[req_id])

                self.logger.info(f'collected {num_req}/{self.envelope.num_part[-1]} parts of {type(self.req).__name__}')

                if num_req == self.envelope.num_part[-1]:
                    self._prev_messages = self._pending_msgs.pop(req_id)
                    self._prev_requests = [getattr(v.request, v.request.WhichOneof('body')) for v in self._prev_messages]
                else:
                    raise NoExplicitMessage

                self.reduce(*args, **kwargs)
                self.envelope.num_part.pop(-1)
            else:
                return
        else:
            super().__call__(*args, **kwargs)

    def reduce(self, *args, **kwargs):
        raise NotImplementedError


class MergeDriver(BaseReduceDriver):
    """Merge the routes information from multiple envelopes into one """

    def reduce(self, *args, **kwargs):
        # take unique routes by service identity
        routes = {(r.pod + r.pod_id): r for m in self.prev_msgs for r in m.envelope.routes}
        self.msg.envelope.ClearField('routes')
        self.msg.envelope.routes.extend(
            sorted(routes.values(), key=lambda x: (x.start_time.seconds, x.start_time.nanos)))


class MergeTopKDriver(MergeDriver):
    """Merge the topk results from multiple messages into one and sorted

    Useful in indexer sharding (i.e. ``--replicas > 1``)

    Complexity depends on the level:
         - ``level=chunk``: D x C x K x R
         - ``level=doc``: D x K x R

    where:
        - D is the number of queries
        - C is the number of chunks per query
        - K is the top-k
        - R is the number of shards (i.e. ``--replicas``)
    """

    def __init__(self, level: str, *args, **kwargs):
        """

        :param level: merge level "chunk" or "doc", or "all"
        """
        super().__init__(*args, **kwargs)
        self.level = level

    def reduce(self, *args, **kwargs):
        if self.level == 'chunk':
            for _d_id, _doc in enumerate(self.req.docs):
                for _c_id, _chunk in enumerate(_doc.chunks):
                    _flat_topk = [k for r in self.prev_reqs for k in r.docs[_d_id].chunks[_c_id].topk_results]
                    _chunk.ClearField('topk_results')
                    _chunk.topk_results.extend(sorted(_flat_topk, key=lambda x: x.score.value))
        elif self.level == 'doc':
            for _d_id, _doc in enumerate(self.req.docs):
                _flat_topk = [k for r in self.prev_reqs for k in r.docs[_d_id].topk_results]
                _doc.ClearField('topk_results')
                _doc.topk_results.extend(sorted(_flat_topk, key=lambda x: x.score.value))
        elif self.level == 'all':
            for _d_id, _doc in enumerate(self.req.docs):
                _flat_topk = [k for r in self.prev_reqs for k in r.docs[_d_id].topk_results]
                _doc.ClearField('topk_results')
                _doc.topk_results.extend(sorted(_flat_topk, key=lambda x: x.score.value))

                for _c_id, _chunk in enumerate(_doc.chunks):
                    _flat_topk = [k for r in self.prev_reqs for k in r.docs[_d_id].chunks[_c_id].topk_results]
                    _chunk.ClearField('topk_results')
                    _chunk.topk_results.extend(sorted(_flat_topk, key=lambda x: x.score.value))

        else:
            raise TypeError(f'level={self.level} is not supported, must choose from "chunk" or "doc" ')

        super().reduce(*args, **kwargs)


class ChunkMergeTopKDriver(MergeTopKDriver):
    """A shortcut to :class:`MergeTopKDriver` with ``level=chunk``"""

    def __init__(self, level: str = 'chunk', *args, **kwargs):
        super().__init__(level, *args, **kwargs)


class DocMergeTopKDriver(MergeTopKDriver):
    """A shortcut to :class:`MergeTopKDriver` with ``level=doc``"""

    def __init__(self, level: str = 'doc', *args, **kwargs):
        super().__init__(level, *args, **kwargs)
