import os
import sys
import time

from check_serializing.dummy_pb2 import BytesWrapper, DocsWrapper
from docarray import DocumentArray, Document
from docarray.proto.docarray_pb2 import DocumentProto

DOC_SIZE = 1042 * 100
DOC_COUNT = 10000
da = DocumentArray(
    [
        DocumentProto(buffer=bytes(bytearray(os.urandom(DOC_SIZE))))
        for _ in range(DOC_COUNT)
    ]
)


def serialize_bytes_wrapper():
    return BytesWrapper(docs=da.to_bytes()).SerializeToString()


def deserialize_bytes_wrapper(proto_byte_array):
    loaded_bw = BytesWrapper()
    loaded_bw.ParseFromString(proto_byte_array)
    return DocumentArray.load_binary(loaded_bw.docs)


def serialize_doc_wrapper():
    dw = DocsWrapper()
    for d in da:
        dw.docs.append(d.proto)
    return dw.SerializeToString()


def deserialize_doc_wrapper(proto_byte_array):
    loaded_dw = DocsWrapper()
    loaded_dw.ParseFromString(proto_byte_array)
    return loaded_dw.docs


start_bw_serializer = time.time()
proto_byte_array = serialize_bytes_wrapper()
end_bw_serializer = time.time()

start_bw_deserializer = time.time()
loaded_da = deserialize_bytes_wrapper(proto_byte_array)
end_bw_deserializer = time.time()

print(
    f'Byte array proto serialization took {end_bw_serializer-start_bw_serializer}, deserialization took {end_bw_deserializer-start_bw_deserializer} and serialized size is {sys.getsizeof(proto_byte_array)} - loaded da has {len(loaded_da)} docs'
)

start_dw_serializer = time.time()
proto_byte_array = serialize_doc_wrapper()
end_dw_serializer = time.time()

start_dw_deserializer = time.time()
loaded_da = deserialize_doc_wrapper(proto_byte_array)
end_dw_deserializer = time.time()

print(
    f'Doc array proto serialization took {end_dw_serializer-start_dw_serializer}, deserialization took {end_dw_deserializer-start_dw_deserializer} and serialized size is {sys.getsizeof(proto_byte_array)} - loaded da has {len(loaded_da)} docs'
)
