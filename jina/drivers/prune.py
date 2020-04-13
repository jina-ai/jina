from . import BaseDriver


class ChunkPruneDriver(BaseDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    Removed fields are ``embedding``, ``raw_bytes``, ``blob``, ``text``.
    """

    def __init__(self, pruned=('embedding', 'raw_bytes', 'blob', 'text'), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pruned = pruned

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for c in d.chunks:
                for k in self.pruned:
                    c.ClearField(k)


class DocPruneDriver(BaseDriver):
    """Clean some fields from the doc-level protobuf to reduce the total size of request

    Removed fields are ``chunks``
    """

    def __init__(self, pruned=('chunks',), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pruned = pruned

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for k in self.pruned:
                d.ClearField(k)


class ReqPruneDriver(BaseDriver):
    """Clean up request from the protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __call__(self, *args, **kwargs):
        self.msg.ClearField('request')
