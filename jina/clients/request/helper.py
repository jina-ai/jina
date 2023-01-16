"""Module for helper functions for clients."""
from typing import Optional, Tuple

from docarray.documents.legacy import Document, DocumentArray

from jina.enums import DataInputType
from jina.types.request.data import DataRequest


def _new_data_request_from_batch(
    batch,
    data_type: DataInputType,
    endpoint: str,
    target: Optional[str],
    parameters: Optional[dict],
) -> DataRequest:
    req = _new_data_request(endpoint, target, parameters)

    # add docs fields
    _add_docs(req, batch, data_type)

    return req


def _new_data_request(
    endpoint: str, target: Optional[str], parameters: Optional[dict]
) -> DataRequest:
    req = DataRequest()

    # set up header
    req.header.exec_endpoint = endpoint
    if target:
        req.header.target_executor = target
    # add parameters field
    if parameters:
        req.parameters = parameters
    return req


def _new_doc_from_data(
    data, data_type: DataInputType
) -> Tuple['Document', 'DataInputType']:

    if data_type == DataInputType.DICT:
        return Document(**data), DataInputType.DICT
    if data_type == DataInputType.AUTO or data_type == DataInputType.DOCUMENT:
        if isinstance(data, Document):
            # if incoming is already primitive type Document, then all good, best practice!
            return data, DataInputType.DOCUMENT
        elif isinstance(data, dict):
            return Document(**data), DataInputType.DICT
        else:
            d = Document(data)
            return d, DataInputType.DOCUMENT  # NOT HIT


def _add_docs(req: DataRequest, batch, data_type: DataInputType) -> None:
    da = DocumentArray([])
    for content in batch:
        d, data_type = _new_doc_from_data(content, data_type)
        da.append(d)
    req.data.docs = da
