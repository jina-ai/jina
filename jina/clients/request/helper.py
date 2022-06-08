"""Module for helper functions for clients."""
from typing import Tuple

from docarray import Document, DocumentArray
from jina.enums import DataInputType
from jina.types.request.data import DataRequest


def _new_data_request_from_batch(
    _kwargs, batch, data_type, endpoint, target, parameters
):
    req = _new_data_request(endpoint, target, parameters)

    # add docs fields
    _add_docs(req, batch, data_type, _kwargs)

    return req


def _new_data_request(endpoint, target, parameters):
    req = DataRequest()

    # set up header
    if endpoint:
        req.header.exec_endpoint = endpoint
    if target:
        req.header.target_executor = target
    # add parameters field
    if parameters:
        req.parameters = parameters
    return req


def _new_doc_from_data(
    data, data_type: DataInputType, **kwargs
) -> Tuple['Document', 'DataInputType']:
    def _build_doc_from_content():
        return Document(content=data, **kwargs), DataInputType.CONTENT

    if data_type == DataInputType.DICT:
        doc = Document.from_dict(data)
        return doc, DataInputType.DICT
    if data_type == DataInputType.AUTO or data_type == DataInputType.DOCUMENT:
        if isinstance(data, Document):
            # if incoming is already primitive type Document, then all good, best practice!
            return data, DataInputType.DOCUMENT
        elif isinstance(data, dict):
            return Document.from_dict(data), DataInputType.DICT
        try:
            d = Document(data, **kwargs)
            return d, DataInputType.DOCUMENT
        except ValueError:
            # AUTO has a fallback, now reconsider it as content
            if data_type == DataInputType.AUTO:
                return _build_doc_from_content()
            else:
                raise
    elif data_type == DataInputType.CONTENT:
        return _build_doc_from_content()


def _add_docs(req, batch, data_type, _kwargs):
    da = DocumentArray()
    for content in batch:
        if isinstance(content, tuple) and len(content) == 2:
            d, data_type = _new_doc_from_data(content[0], data_type, **_kwargs)
            gt, _ = _new_doc_from_data(content[1], data_type, **_kwargs)
            da.append(d)
        else:
            d, data_type = _new_doc_from_data(content, data_type, **_kwargs)
            da.append(d)
    req.data.docs = da
