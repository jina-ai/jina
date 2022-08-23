"""
The :mod:`jina.proto` defines the protobuf used in jina. It is the core message protocol used in communicating between :class:`jina.orchestrate.deployments.BaseDeployment`. It also defines the interface of a gRPC service.

"""

from google.protobuf import __version__ as __pb__version__

if __pb__version__.startswith('4'):
    from .pb import jina_pb2, jina_pb2_grpc
else:
    from .pb2 import jina_pb2, jina_pb2_grpc
