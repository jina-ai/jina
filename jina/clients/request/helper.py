from typing import Tuple, Sequence

from ... import Document, Request
from ...enums import DataInputType
from ...excepts import BadDocType


def _new_doc_from_data(data, data_type: DataInputType, **kwargs) -> Tuple['Document', 'DataInputType']:
    def _build_doc_from_content():
        with Document(**kwargs) as d:
            d.content = data
        return d, DataInputType.CONTENT

    if data_type == DataInputType.AUTO or data_type == DataInputType.DOCUMENT:
        if isinstance(data, Document):
            # if incoming is already primitive type Document, then all good, best practice!
            return data, DataInputType.DOCUMENT
        try:
            d = Document(data, **kwargs)
            return d, DataInputType.DOCUMENT
        except BadDocType:
            # AUTO has a fallback, now reconsider it as content
            if data_type == DataInputType.AUTO:
                return _build_doc_from_content()
            else:
                raise
    elif data_type == DataInputType.CONTENT:
        return _build_doc_from_content()


def _new_request_from_batch(_kwargs, batch, data_type, mode, queryset):
    req = Request()
    req.request_type = str(mode)
    for content in batch:
        if isinstance(content, tuple) and len(content) == 2:
            # content comes in pair,  will take the first as the input and the second as the groundtruth

            # note how data_type is cached
            d, data_type = _new_doc_from_data(content[0], data_type, **_kwargs)
            gt, _ = _new_doc_from_data(content[1], data_type, **_kwargs)
            req.docs.append(d)
            req.groundtruths.append(gt)
        else:
            d, data_type = _new_doc_from_data(content, data_type, **_kwargs)
            req.docs.append(d)
    if isinstance(queryset, Sequence):
        req.queryset.extend(queryset)
    elif queryset is not None:
        req.queryset.append(queryset)
    return req
