# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: jina.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\njina.proto\x12\x04jina\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1cgoogle/protobuf/struct.proto\"A\n\x11\x44\x65nseNdArrayProto\x12\x0e\n\x06\x62uffer\x18\x01 \x01(\x0c\x12\r\n\x05shape\x18\x02 \x03(\r\x12\r\n\x05\x64type\x18\x03 \x01(\t\"\xae\x01\n\x0cNdArrayProto\x12(\n\x05\x64\x65nse\x18\x01 \x01(\x0b\x32\x17.jina.DenseNdArrayProtoH\x00\x12*\n\x06sparse\x18\x02 \x01(\x0b\x32\x18.jina.SparseNdArrayProtoH\x00\x12\x10\n\x08\x63ls_name\x18\x03 \x01(\t\x12+\n\nparameters\x18\x04 \x01(\x0b\x32\x17.google.protobuf.StructB\t\n\x07\x63ontent\"v\n\x12SparseNdArrayProto\x12(\n\x07indices\x18\x01 \x01(\x0b\x32\x17.jina.DenseNdArrayProto\x12\'\n\x06values\x18\x02 \x01(\x0b\x32\x17.jina.DenseNdArrayProto\x12\r\n\x05shape\x18\x03 \x03(\r\"\x7f\n\x0fNamedScoreProto\x12\r\n\x05value\x18\x01 \x01(\x02\x12\x0f\n\x07op_name\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\'\n\x08operands\x18\x04 \x03(\x0b\x32\x15.jina.NamedScoreProto\x12\x0e\n\x06ref_id\x18\x05 \x01(\t\"w\n\nGraphProto\x12%\n\tadjacency\x18\x01 \x01(\x0b\x32\x12.jina.NdArrayProto\x12.\n\redge_features\x18\x02 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x12\n\nundirected\x18\x03 \x01(\x08\"\xc4\x05\n\rDocumentProto\x12\n\n\x02id\x18\x01 \x01(\t\x12\x13\n\x0bgranularity\x18\x0e \x01(\r\x12\x11\n\tadjacency\x18\x16 \x01(\r\x12\x11\n\tparent_id\x18\x10 \x01(\t\x12\x10\n\x06\x62uffer\x18\x03 \x01(\x0cH\x00\x12\"\n\x04\x62lob\x18\x0c \x01(\x0b\x32\x12.jina.NdArrayProtoH\x00\x12\x0e\n\x04text\x18\r \x01(\tH\x00\x12!\n\x05graph\x18\x1b \x01(\x0b\x32\x10.jina.GraphProtoH\x00\x12#\n\x06\x63hunks\x18\x04 \x03(\x0b\x32\x13.jina.DocumentProto\x12\x0e\n\x06weight\x18\x05 \x01(\x02\x12$\n\x07matches\x18\x08 \x03(\x0b\x32\x13.jina.DocumentProto\x12\x0b\n\x03uri\x18\t \x01(\t\x12\x11\n\tmime_type\x18\n \x01(\t\x12%\n\x04tags\x18\x0b \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x10\n\x08location\x18\x11 \x03(\r\x12\x0e\n\x06offset\x18\x12 \x01(\r\x12%\n\tembedding\x18\x13 \x01(\x0b\x32\x12.jina.NdArrayProto\x12/\n\x06scores\x18\x1c \x03(\x0b\x32\x1f.jina.DocumentProto.ScoresEntry\x12\x10\n\x08modality\x18\x15 \x01(\t\x12\x39\n\x0b\x65valuations\x18\x1d \x03(\x0b\x32$.jina.DocumentProto.EvaluationsEntry\x1a\x44\n\x0bScoresEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12$\n\x05value\x18\x02 \x01(\x0b\x32\x15.jina.NamedScoreProto:\x02\x38\x01\x1aI\n\x10\x45valuationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12$\n\x05value\x18\x02 \x01(\x0b\x32\x15.jina.NamedScoreProto:\x02\x38\x01\x42\t\n\x07\x63ontent\"\xaa\x01\n\nRouteProto\x12\x0b\n\x03pod\x18\x01 \x01(\t\x12\x0e\n\x06pod_id\x18\x02 \x01(\t\x12.\n\nstart_time\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12,\n\x08\x65nd_time\x18\x04 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12!\n\x06status\x18\x05 \x01(\x0b\x32\x11.jina.StatusProto\"\xf7\x03\n\rEnvelopeProto\x12\x11\n\tsender_id\x18\x01 \x01(\t\x12\x13\n\x0breceiver_id\x18\x02 \x01(\t\x12\x12\n\nrequest_id\x18\x03 \x01(\t\x12\x0f\n\x07timeout\x18\x04 \x01(\r\x12\x31\n\x07version\x18\x05 \x01(\x0b\x32 .jina.EnvelopeProto.VersionProto\x12\x14\n\x0crequest_type\x18\x06 \x01(\t\x12\x15\n\rcheck_version\x18\x07 \x01(\x08\x12<\n\x0b\x63ompression\x18\x08 \x01(\x0b\x32\'.jina.EnvelopeProto.CompressConfigProto\x12!\n\x06status\x18\t \x01(\x0b\x32\x11.jina.StatusProto\x12!\n\x06header\x18\n \x01(\x0b\x32\x11.jina.HeaderProto\x1a\x38\n\x0cVersionProto\x12\x0c\n\x04jina\x18\x01 \x01(\t\x12\r\n\x05proto\x18\x02 \x01(\t\x12\x0b\n\x03vcs\x18\x03 \x01(\t\x1a{\n\x13\x43ompressConfigProto\x12\x11\n\talgorithm\x18\x01 \x01(\t\x12\x11\n\tmin_bytes\x18\x02 \x01(\x04\x12\x11\n\tmin_ratio\x18\x03 \x01(\x02\x12+\n\nparameters\x18\x04 \x01(\x0b\x32\x17.google.protobuf.Struct\"Q\n\x0bHeaderProto\x12\x15\n\rexec_endpoint\x18\x01 \x01(\t\x12\x15\n\rtarget_peapod\x18\x02 \x01(\t\x12\x14\n\x0cno_propagate\x18\x03 \x01(\x08\"\xcf\x02\n\x0bStatusProto\x12*\n\x04\x63ode\x18\x01 \x01(\x0e\x32\x1c.jina.StatusProto.StatusCode\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x33\n\texception\x18\x03 \x01(\x0b\x32 .jina.StatusProto.ExceptionProto\x1aN\n\x0e\x45xceptionProto\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x02 \x03(\t\x12\x0e\n\x06stacks\x18\x03 \x03(\t\x12\x10\n\x08\x65xecutor\x18\x04 \x01(\t\"z\n\nStatusCode\x12\x0b\n\x07SUCCESS\x10\x00\x12\x0b\n\x07PENDING\x10\x01\x12\t\n\x05READY\x10\x02\x12\t\n\x05\x45RROR\x10\x03\x12\x13\n\x0f\x45RROR_DUPLICATE\x10\x04\x12\x14\n\x10\x45RROR_NOTALLOWED\x10\x05\x12\x11\n\rERROR_CHAINED\x10\x06\"Z\n\x0cMessageProto\x12%\n\x08\x65nvelope\x18\x01 \x01(\x0b\x32\x13.jina.EnvelopeProto\x12#\n\x07request\x18\x02 \x01(\x0b\x32\x12.jina.RequestProto\"8\n\x10MessageListProto\x12$\n\x08messages\x18\x01 \x03(\x0b\x32\x12.jina.MessageProto\"7\n\x12\x44ocumentArrayProto\x12!\n\x04\x64ocs\x18\x01 \x03(\x0b\x32\x13.jina.DocumentProto\"^\n\rRelatedEntity\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07\x61\x64\x64ress\x18\x02 \x01(\t\x12\x0c\n\x04port\x18\x03 \x01(\r\x12\x15\n\x08shard_id\x18\x04 \x01(\rH\x00\x88\x01\x01\x42\x0b\n\t_shard_id\"\xe7\x04\n\x0cRequestProto\x12\x12\n\nrequest_id\x18\x01 \x01(\t\x12\x39\n\x07\x63ontrol\x18\x02 \x01(\x0b\x32&.jina.RequestProto.ControlRequestProtoH\x00\x12\x33\n\x04\x64\x61ta\x18\x03 \x01(\x0b\x32#.jina.RequestProto.DataRequestProtoH\x00\x12!\n\x06header\x18\x04 \x01(\x0b\x32\x11.jina.HeaderProto\x12+\n\nparameters\x18\x05 \x01(\x0b\x32\x17.google.protobuf.Struct\x12 \n\x06routes\x18\x06 \x03(\x0b\x32\x10.jina.RouteProto\x12!\n\x06status\x18\x07 \x01(\x0b\x32\x11.jina.StatusProto\x1a`\n\x10\x44\x61taRequestProto\x12!\n\x04\x64ocs\x18\x01 \x03(\x0b\x32\x13.jina.DocumentProto\x12)\n\x0cgroundtruths\x18\x02 \x03(\x0b\x32\x13.jina.DocumentProto\x1a\xd3\x01\n\x13\x43ontrolRequestProto\x12?\n\x07\x63ommand\x18\x01 \x01(\x0e\x32..jina.RequestProto.ControlRequestProto.Command\x12,\n\x0frelatedEntities\x18\x02 \x03(\x0b\x32\x13.jina.RelatedEntity\"M\n\x07\x43ommand\x12\r\n\tTERMINATE\x10\x00\x12\n\n\x06STATUS\x10\x01\x12\t\n\x05SCALE\x10\x02\x12\x0c\n\x08\x41\x43TIVATE\x10\x03\x12\x0e\n\nDEACTIVATE\x10\x04\x42\x06\n\x04\x62ody2?\n\x07JinaRPC\x12\x34\n\x04\x43\x61ll\x12\x12.jina.RequestProto\x1a\x12.jina.RequestProto\"\x00(\x01\x30\x01\x32J\n\x12JinaDataRequestRPC\x12\x34\n\x04\x43\x61ll\x12\x16.jina.MessageListProto\x1a\x12.jina.MessageProto\"\x00\x62\x06proto3')



_DENSENDARRAYPROTO = DESCRIPTOR.message_types_by_name['DenseNdArrayProto']
_NDARRAYPROTO = DESCRIPTOR.message_types_by_name['NdArrayProto']
_SPARSENDARRAYPROTO = DESCRIPTOR.message_types_by_name['SparseNdArrayProto']
_NAMEDSCOREPROTO = DESCRIPTOR.message_types_by_name['NamedScoreProto']
_GRAPHPROTO = DESCRIPTOR.message_types_by_name['GraphProto']
_DOCUMENTPROTO = DESCRIPTOR.message_types_by_name['DocumentProto']
_DOCUMENTPROTO_SCORESENTRY = _DOCUMENTPROTO.nested_types_by_name['ScoresEntry']
_DOCUMENTPROTO_EVALUATIONSENTRY = _DOCUMENTPROTO.nested_types_by_name['EvaluationsEntry']
_ROUTEPROTO = DESCRIPTOR.message_types_by_name['RouteProto']
_ENVELOPEPROTO = DESCRIPTOR.message_types_by_name['EnvelopeProto']
_ENVELOPEPROTO_VERSIONPROTO = _ENVELOPEPROTO.nested_types_by_name['VersionProto']
_ENVELOPEPROTO_COMPRESSCONFIGPROTO = _ENVELOPEPROTO.nested_types_by_name['CompressConfigProto']
_HEADERPROTO = DESCRIPTOR.message_types_by_name['HeaderProto']
_STATUSPROTO = DESCRIPTOR.message_types_by_name['StatusProto']
_STATUSPROTO_EXCEPTIONPROTO = _STATUSPROTO.nested_types_by_name['ExceptionProto']
_MESSAGEPROTO = DESCRIPTOR.message_types_by_name['MessageProto']
_MESSAGELISTPROTO = DESCRIPTOR.message_types_by_name['MessageListProto']
_DOCUMENTARRAYPROTO = DESCRIPTOR.message_types_by_name['DocumentArrayProto']
_RELATEDENTITY = DESCRIPTOR.message_types_by_name['RelatedEntity']
_REQUESTPROTO = DESCRIPTOR.message_types_by_name['RequestProto']
_REQUESTPROTO_DATAREQUESTPROTO = _REQUESTPROTO.nested_types_by_name['DataRequestProto']
_REQUESTPROTO_CONTROLREQUESTPROTO = _REQUESTPROTO.nested_types_by_name['ControlRequestProto']
_STATUSPROTO_STATUSCODE = _STATUSPROTO.enum_types_by_name['StatusCode']
_REQUESTPROTO_CONTROLREQUESTPROTO_COMMAND = _REQUESTPROTO_CONTROLREQUESTPROTO.enum_types_by_name['Command']
DenseNdArrayProto = _reflection.GeneratedProtocolMessageType('DenseNdArrayProto', (_message.Message,), {
  'DESCRIPTOR' : _DENSENDARRAYPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.DenseNdArrayProto)
  })
_sym_db.RegisterMessage(DenseNdArrayProto)

NdArrayProto = _reflection.GeneratedProtocolMessageType('NdArrayProto', (_message.Message,), {
  'DESCRIPTOR' : _NDARRAYPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.NdArrayProto)
  })
_sym_db.RegisterMessage(NdArrayProto)

SparseNdArrayProto = _reflection.GeneratedProtocolMessageType('SparseNdArrayProto', (_message.Message,), {
  'DESCRIPTOR' : _SPARSENDARRAYPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.SparseNdArrayProto)
  })
_sym_db.RegisterMessage(SparseNdArrayProto)

NamedScoreProto = _reflection.GeneratedProtocolMessageType('NamedScoreProto', (_message.Message,), {
  'DESCRIPTOR' : _NAMEDSCOREPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.NamedScoreProto)
  })
_sym_db.RegisterMessage(NamedScoreProto)

GraphProto = _reflection.GeneratedProtocolMessageType('GraphProto', (_message.Message,), {
  'DESCRIPTOR' : _GRAPHPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.GraphProto)
  })
_sym_db.RegisterMessage(GraphProto)

DocumentProto = _reflection.GeneratedProtocolMessageType('DocumentProto', (_message.Message,), {

  'ScoresEntry' : _reflection.GeneratedProtocolMessageType('ScoresEntry', (_message.Message,), {
    'DESCRIPTOR' : _DOCUMENTPROTO_SCORESENTRY,
    '__module__' : 'jina_pb2'
    # @@protoc_insertion_point(class_scope:jina.DocumentProto.ScoresEntry)
    })
  ,

  'EvaluationsEntry' : _reflection.GeneratedProtocolMessageType('EvaluationsEntry', (_message.Message,), {
    'DESCRIPTOR' : _DOCUMENTPROTO_EVALUATIONSENTRY,
    '__module__' : 'jina_pb2'
    # @@protoc_insertion_point(class_scope:jina.DocumentProto.EvaluationsEntry)
    })
  ,
  'DESCRIPTOR' : _DOCUMENTPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.DocumentProto)
  })
_sym_db.RegisterMessage(DocumentProto)
_sym_db.RegisterMessage(DocumentProto.ScoresEntry)
_sym_db.RegisterMessage(DocumentProto.EvaluationsEntry)

RouteProto = _reflection.GeneratedProtocolMessageType('RouteProto', (_message.Message,), {
  'DESCRIPTOR' : _ROUTEPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.RouteProto)
  })
_sym_db.RegisterMessage(RouteProto)

EnvelopeProto = _reflection.GeneratedProtocolMessageType('EnvelopeProto', (_message.Message,), {

  'VersionProto' : _reflection.GeneratedProtocolMessageType('VersionProto', (_message.Message,), {
    'DESCRIPTOR' : _ENVELOPEPROTO_VERSIONPROTO,
    '__module__' : 'jina_pb2'
    # @@protoc_insertion_point(class_scope:jina.EnvelopeProto.VersionProto)
    })
  ,

  'CompressConfigProto' : _reflection.GeneratedProtocolMessageType('CompressConfigProto', (_message.Message,), {
    'DESCRIPTOR' : _ENVELOPEPROTO_COMPRESSCONFIGPROTO,
    '__module__' : 'jina_pb2'
    # @@protoc_insertion_point(class_scope:jina.EnvelopeProto.CompressConfigProto)
    })
  ,
  'DESCRIPTOR' : _ENVELOPEPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.EnvelopeProto)
  })
_sym_db.RegisterMessage(EnvelopeProto)
_sym_db.RegisterMessage(EnvelopeProto.VersionProto)
_sym_db.RegisterMessage(EnvelopeProto.CompressConfigProto)

HeaderProto = _reflection.GeneratedProtocolMessageType('HeaderProto', (_message.Message,), {
  'DESCRIPTOR' : _HEADERPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.HeaderProto)
  })
_sym_db.RegisterMessage(HeaderProto)

StatusProto = _reflection.GeneratedProtocolMessageType('StatusProto', (_message.Message,), {

  'ExceptionProto' : _reflection.GeneratedProtocolMessageType('ExceptionProto', (_message.Message,), {
    'DESCRIPTOR' : _STATUSPROTO_EXCEPTIONPROTO,
    '__module__' : 'jina_pb2'
    # @@protoc_insertion_point(class_scope:jina.StatusProto.ExceptionProto)
    })
  ,
  'DESCRIPTOR' : _STATUSPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.StatusProto)
  })
_sym_db.RegisterMessage(StatusProto)
_sym_db.RegisterMessage(StatusProto.ExceptionProto)

MessageProto = _reflection.GeneratedProtocolMessageType('MessageProto', (_message.Message,), {
  'DESCRIPTOR' : _MESSAGEPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.MessageProto)
  })
_sym_db.RegisterMessage(MessageProto)

MessageListProto = _reflection.GeneratedProtocolMessageType('MessageListProto', (_message.Message,), {
  'DESCRIPTOR' : _MESSAGELISTPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.MessageListProto)
  })
_sym_db.RegisterMessage(MessageListProto)

DocumentArrayProto = _reflection.GeneratedProtocolMessageType('DocumentArrayProto', (_message.Message,), {
  'DESCRIPTOR' : _DOCUMENTARRAYPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.DocumentArrayProto)
  })
_sym_db.RegisterMessage(DocumentArrayProto)

RelatedEntity = _reflection.GeneratedProtocolMessageType('RelatedEntity', (_message.Message,), {
  'DESCRIPTOR' : _RELATEDENTITY,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.RelatedEntity)
  })
_sym_db.RegisterMessage(RelatedEntity)

RequestProto = _reflection.GeneratedProtocolMessageType('RequestProto', (_message.Message,), {

  'DataRequestProto' : _reflection.GeneratedProtocolMessageType('DataRequestProto', (_message.Message,), {
    'DESCRIPTOR' : _REQUESTPROTO_DATAREQUESTPROTO,
    '__module__' : 'jina_pb2'
    # @@protoc_insertion_point(class_scope:jina.RequestProto.DataRequestProto)
    })
  ,

  'ControlRequestProto' : _reflection.GeneratedProtocolMessageType('ControlRequestProto', (_message.Message,), {
    'DESCRIPTOR' : _REQUESTPROTO_CONTROLREQUESTPROTO,
    '__module__' : 'jina_pb2'
    # @@protoc_insertion_point(class_scope:jina.RequestProto.ControlRequestProto)
    })
  ,
  'DESCRIPTOR' : _REQUESTPROTO,
  '__module__' : 'jina_pb2'
  # @@protoc_insertion_point(class_scope:jina.RequestProto)
  })
_sym_db.RegisterMessage(RequestProto)
_sym_db.RegisterMessage(RequestProto.DataRequestProto)
_sym_db.RegisterMessage(RequestProto.ControlRequestProto)

_JINARPC = DESCRIPTOR.services_by_name['JinaRPC']
_JINADATAREQUESTRPC = DESCRIPTOR.services_by_name['JinaDataRequestRPC']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _DOCUMENTPROTO_SCORESENTRY._options = None
  _DOCUMENTPROTO_SCORESENTRY._serialized_options = b'8\001'
  _DOCUMENTPROTO_EVALUATIONSENTRY._options = None
  _DOCUMENTPROTO_EVALUATIONSENTRY._serialized_options = b'8\001'
  _DENSENDARRAYPROTO._serialized_start=83
  _DENSENDARRAYPROTO._serialized_end=148
  _NDARRAYPROTO._serialized_start=151
  _NDARRAYPROTO._serialized_end=325
  _SPARSENDARRAYPROTO._serialized_start=327
  _SPARSENDARRAYPROTO._serialized_end=445
  _NAMEDSCOREPROTO._serialized_start=447
  _NAMEDSCOREPROTO._serialized_end=574
  _GRAPHPROTO._serialized_start=576
  _GRAPHPROTO._serialized_end=695
  _DOCUMENTPROTO._serialized_start=698
  _DOCUMENTPROTO._serialized_end=1406
  _DOCUMENTPROTO_SCORESENTRY._serialized_start=1252
  _DOCUMENTPROTO_SCORESENTRY._serialized_end=1320
  _DOCUMENTPROTO_EVALUATIONSENTRY._serialized_start=1322
  _DOCUMENTPROTO_EVALUATIONSENTRY._serialized_end=1395
  _ROUTEPROTO._serialized_start=1409
  _ROUTEPROTO._serialized_end=1579
  _ENVELOPEPROTO._serialized_start=1582
  _ENVELOPEPROTO._serialized_end=2085
  _ENVELOPEPROTO_VERSIONPROTO._serialized_start=1904
  _ENVELOPEPROTO_VERSIONPROTO._serialized_end=1960
  _ENVELOPEPROTO_COMPRESSCONFIGPROTO._serialized_start=1962
  _ENVELOPEPROTO_COMPRESSCONFIGPROTO._serialized_end=2085
  _HEADERPROTO._serialized_start=2087
  _HEADERPROTO._serialized_end=2168
  _STATUSPROTO._serialized_start=2171
  _STATUSPROTO._serialized_end=2506
  _STATUSPROTO_EXCEPTIONPROTO._serialized_start=2304
  _STATUSPROTO_EXCEPTIONPROTO._serialized_end=2382
  _STATUSPROTO_STATUSCODE._serialized_start=2384
  _STATUSPROTO_STATUSCODE._serialized_end=2506
  _MESSAGEPROTO._serialized_start=2508
  _MESSAGEPROTO._serialized_end=2598
  _MESSAGELISTPROTO._serialized_start=2600
  _MESSAGELISTPROTO._serialized_end=2656
  _DOCUMENTARRAYPROTO._serialized_start=2658
  _DOCUMENTARRAYPROTO._serialized_end=2713
  _RELATEDENTITY._serialized_start=2715
  _RELATEDENTITY._serialized_end=2809
  _REQUESTPROTO._serialized_start=2812
  _REQUESTPROTO._serialized_end=3427
  _REQUESTPROTO_DATAREQUESTPROTO._serialized_start=3109
  _REQUESTPROTO_DATAREQUESTPROTO._serialized_end=3205
  _REQUESTPROTO_CONTROLREQUESTPROTO._serialized_start=3208
  _REQUESTPROTO_CONTROLREQUESTPROTO._serialized_end=3419
  _REQUESTPROTO_CONTROLREQUESTPROTO_COMMAND._serialized_start=3342
  _REQUESTPROTO_CONTROLREQUESTPROTO_COMMAND._serialized_end=3419
  _JINARPC._serialized_start=3429
  _JINARPC._serialized_end=3492
  _JINADATAREQUESTRPC._serialized_start=3494
  _JINADATAREQUESTRPC._serialized_end=3568
# @@protoc_insertion_point(module_scope)
