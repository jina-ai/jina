from google.protobuf import __version__ as __pb__version__

from jina._docarray import docarray_v2 as is_docarray_v2

if __pb__version__.startswith('4'):
    if is_docarray_v2:
        from .docarray_v2.pb.jina_pb2 import *
    else:
        from .docarray_v1.pb.jina_pb2 import *

else:
    if is_docarray_v2:
        from .docarray_v2.pb2.jina_pb2 import *
    else:
        from .docarray_v1.pb2.jina_pb2 import *
