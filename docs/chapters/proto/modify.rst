Update Protocol Specification
=============================




For developers who want to change the protobuf specification, one needs to first edit :file:`jina/proto/jina.proto` and then use :file:`jina/proto/build-proto.sh` to regenerate the python interfaces (i.e. :file:`jina/proto/jina_pb2.py` and :file:`jina/proto/jina_pb2_grpc.py`).

.. note::
    Starting 0.7.5, we provide a Docker image for you to generate Protobuf interface in the containerized environment. That means you don't need to config the build protobuf/grpc environment locally. Simply use :command:`docker run -v $(pwd)/jina/proto:/jina/proto jinaai/protogen` where ``$(pwd)`` is your Jina repository root.

Take MacOS as an example,

#. Download :file:`protoc-$VERSION-$PLATFORM.zip` from `the official Github site <https://github.com/protocolbuffers/protobuf/releases/>`_ and decompress it.

#. Copy the binary file and include to your system path:

    .. highlight:: bash
    .. code-block:: bash

       cp ~/Downloads/protoc-3.7.1-osx-x86_64/bin/protoc /usr/local/bin/

       cp -r ~/Downloads/protoc-3.7.1-osx-x86_64/include/* /usr/local/include/


#. Install gRPC tools dependencies:

    .. highlight:: bash
    .. code-block:: bash

        brew install automake autoconf libtool

#. Install gRPC and ``grpc_python_plugin`` from the source:

    .. highlight:: bash
    .. code-block:: bash

       git clone https://github.com/grpc/grpc.git
       git submodule update --init
       make grpc_python_plugin


#. This will compile the grpc-python-plugin and build it to, e.g., :file:`~/Documents/grpc/bins/opt/grpc_python_plugin`

#. Generate the python interfaces.

    .. highlight:: bash
    .. code-block:: bash

        cd jina/proto
        bash build-proto.sh ~/Documents/grpc/bins/opt/grpc_python_plugin