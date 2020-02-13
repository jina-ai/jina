from ..helper import array2blob, pb_obj2dict


def handler_chunk_transform(exec_fn, pea, req, *args, **kwargs):
    """Transform the chunk-level information on given keys using the executor

    It requires ``ctx`` has :class:`jina.executors.transformers.BaseChunkTransformer` equipped
    """
    no_chunk_docs = []

    for d in req.docs:
        if not d.chunks:
            no_chunk_docs.append(d.doc_id)
            continue
        for c in d.chunks:
            ret = exec_fn(**pb_obj2dict(c, pea.executor.required_keys))
            for k, v in ret.items():
                setattr(c, k, v)

    if no_chunk_docs:
        pea.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)


def handler_doc_transform(exec_fn, pea, req, *args, **kwargs):
    """Transform the doc-level information on given keys using the executor

    It requires ``ctx`` has :class:`jina.executors.transformers.BaseDocTransformer` equipped
    """
    for d in req.docs:
        ret = exec_fn.transform(**pb_obj2dict(d, pea.executor.required_keys))
        for k, v in ret.items():
            setattr(d, k, v)


def handler_segment(exec_fn, pea, req, *args, **kwargs):
    """Segment document into chunk using the executor

    It requires ``ctx`` has :class:`jina.executors.transformers.BaseSegmenter` equipped
    """
    for d in req.docs:
        ret = exec_fn(**pb_obj2dict(d, pea.executor.required_keys))
        if ret:
            for r in ret:
                c = d.chunks.add()
                for k, v in r.items():
                    if k == 'blob':
                        c.blob.CopyFrom(array2blob(v))
                    else:
                        setattr(c, k, v)
                c.length = len(ret)
            d.length = len(ret)
        else:
            pea.logger.warning('doc %d gives no chunk' % d.doc_id)
