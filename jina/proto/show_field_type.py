""" A helper script for showing the type of each field
"""

from collections import defaultdict
from pprint import pprint

from jina.proto import jina_pb2

if __name__ == '__main__':

    type_field_map = defaultdict(list)
    desc = jina_pb2.Request.DESCRIPTOR.fields_by_name
    print(desc.keys())
    for (field_name, field_descriptor) in desc.items():
        if field_descriptor.message_type:
            # Composite field
            type_field_map[field_descriptor.message_type.name].append(field_name)

        else:
            type_field_map[field_descriptor.type].append(field_name)

    # checkout type-mapping for details
    # https://github.com/protocolbuffers/protobuf/blob/master/python/google/protobuf/descriptor.py

    pprint(type_field_map)

    _trigger_body_fields = set(kk
                               for v in [jina_pb2.Request.IndexRequest,
                                         jina_pb2.Request.SearchRequest,
                                         jina_pb2.Request.TrainRequest,
                                         jina_pb2.Request.ControlRequest] for kk in v.DESCRIPTOR.fields_by_name.keys())
    _trigger_req_fields = set(jina_pb2.Request.DESCRIPTOR.fields_by_name.keys()).difference(
        {'train', 'index', 'search', 'control'})

    print(_trigger_req_fields)
