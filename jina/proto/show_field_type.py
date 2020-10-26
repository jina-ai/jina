""" A helper script for showing the type of each field
"""

from collections import defaultdict
from pprint import pprint

from jina.proto import jina_pb2

type_field_map = defaultdict(list)
desc = jina_pb2.Document.DESCRIPTOR.fields_by_name

for (field_name, field_descriptor) in desc.items():
    if field_descriptor.message_type:
        # Composite field
        type_field_map[field_descriptor.message_type.name].append(field_name)

    else:
        type_field_map[field_descriptor.type].append(field_name)

# checkout type-mapping for details
# https://github.com/protocolbuffers/protobuf/blob/master/python/google/protobuf/descriptor.py

pprint(type_field_map)
