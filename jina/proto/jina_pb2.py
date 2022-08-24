from google.protobuf import __version__ as __pb__version__

if __pb__version__.startswith('4'):
    from .pb.jina_pb2 import *
else:
    from .pb2.jina_pb2 import *
