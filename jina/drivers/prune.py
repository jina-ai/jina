from . import BaseDriver


class ChunkPruneDriver(BaseDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    Removed fields are ``embedding``, ``raw_bytes``, ``blob``, ``text``.
    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for c in d.chunks:
                for k in ('embedding', 'raw_bytes', 'blob', 'text'):
                    c.ClearField(k)


class DocPruneDriver(BaseDriver):
    """Clean some fields from the doc-level protobuf to reduce the total size of request

    Removed fields are ``chunks``
    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for k in ('chunks',):
                d.ClearField(k)


class ReqPruneDriver(BaseDriver):
    """Clean up request from the protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __call__(self, *args, **kwargs):
        self.msg.ClearField('request')
