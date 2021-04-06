"""Module for helper functions for clients."""
from typing import Tuple, Sequence

from ... import Document, Request
from ...enums import DataInputType, RequestType
from ...excepts import BadDocType, BadRequestType
from ...excepts import RequestTypeError


def _new_doc_from_data(
    data, data_type: DataInputType, **kwargs
) -> Tuple['Document', 'DataInputType']:
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


def _new_request_from_batch(_kwargs, batch, data_type, mode, queryset, **kwargs):
    req = Request()
    req.request_type = str(mode)

    try:
        # add type-specific fields
        if (
            mode == RequestType.INDEX
            or mode == RequestType.SEARCH
            or mode == RequestType.TRAIN
            or mode == RequestType.UPDATE
        ):
            if 'extra_kwargs' in _kwargs:
                _kwargs.pop('extra_kwargs')  #: data request do not need extra kwargs
            _add_docs_groundtruths(req, batch, data_type, _kwargs)
        elif mode == RequestType.DELETE:
            _add_ids(req, batch)
        elif mode == RequestType.CONTROL:
            _add_control_propagate(req, _kwargs)
        else:
            raise RequestTypeError(
                f'generating request from {mode} is not yet supported'
            )
    except Exception as ex:
        raise BadRequestType(
            f'error when building {req.request_type} from {batch}'
        ) from ex

    # add common fields
    if isinstance(queryset, Sequence):
        req.queryset.extend(queryset)
    elif queryset is not None:
        req.queryset.append(queryset)
    return req


def _add_docs_groundtruths(req, batch, data_type, _kwargs):
    for content in batch:
        if isinstance(content, tuple) and len(content) == 2:
            # content comes in pair,  will take the first as the input and the second as the ground truth

            # note how data_type is cached
            d, data_type = _new_doc_from_data(content[0], data_type, **_kwargs)
            gt, _ = _new_doc_from_data(content[1], data_type, **_kwargs)
            req.docs.append(d)
            req.groundtruths.append(gt)
        else:
            d, data_type = _new_doc_from_data(content, data_type, **_kwargs)
            req.docs.append(d)


def _add_ids(req, batch):
    string_ids = (str(doc_id) for doc_id in batch)
    req.ids.extend(string_ids)


def _add_control_propagate(req, kwargs):
    from ...proto import jina_pb2

    extra_kwargs = kwargs[
        'extra_kwargs'
    ]  #: control command and args are stored inside extra_kwargs
    _available_commands = dict(
        jina_pb2.RequestProto.ControlRequestProto.DESCRIPTOR.enum_values_by_name
    )

    if 'command' in extra_kwargs:
        command = extra_kwargs['command']
    else:
        raise BadRequestType(
            'sending ControlRequest from Client must contain the field `command`'
        )

    if command in _available_commands:
        req.control.command = getattr(
            jina_pb2.RequestProto.ControlRequestProto, command
        )
    else:
        raise ValueError(
            f'command "{command}" is not supported, must be one of {_available_commands}'
        )
    req.targets.extend(extra_kwargs.get('targets', []))
    req.control.propagate = True
