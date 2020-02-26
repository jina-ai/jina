from . import BaseExecutableDriver
from .helper import array2blob, pb_obj2dict


class ChunkTransformDriver(BaseExecutableDriver):
    """Transform the chunk-level information on given keys using the executor

    """

    def __call__(self, *args, **kwargs):
        no_chunk_docs = []

        for d in self.req.docs:
            if not d.chunks:
                no_chunk_docs.append(d.doc_id)
                continue
            for c in d.chunks:
                ret = self.exec_fn(**pb_obj2dict(c, self.exec.required_keys))
                for k, v in ret.items():
                    setattr(c, k, v)

        if no_chunk_docs:
            self.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)


class DocTransformDriver(BaseExecutableDriver):
    """Transform the doc-level information on given keys using the executor

    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            ret = self.exec_fn(**pb_obj2dict(d, self.exec.required_keys))
            for k, v in ret.items():
                setattr(d, k, v)


class SegmentDriver(BaseExecutableDriver):
    """Segment document into chunks using the executor

    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            ret = self.exec_fn(**pb_obj2dict(d, self.exec.required_keys))
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
                self.logger.warning('doc %d gives no chunk' % d.doc_id)
