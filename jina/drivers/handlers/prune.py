def handler_prune_chunk(exec_fn, pea, req, *args, **kwargs):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    Removed fields are ``embedding``, ``raw_bytes``, ``blob``, ``text``.
    """
    for d in req.docs:
        for c in d.chunks:
            for k in ('embedding', 'raw_bytes', 'blob', 'text'):
                c.ClearField(k)


def handler_prune_doc(exec_fn, pea, req, *args, **kwargs):
    """Clean some fields from the doc-level protobuf to reduce the total size of request

    Removed fields are ``chunks``
    """
    for d in req.docs:
        for k in ('chunks',):
            d.ClearField(k)


def handler_prune_req(exec_fn, pea, req, msg, *args, **kwargs):
    """Clean up request from the protobuf message to reduce the total size of the message

    This is often useful when the proceeding Pods require only a signal, not the full message.
    """
    msg.ClearField('request')
