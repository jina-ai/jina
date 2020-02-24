JEP 1 --- Refactoring ``Driver``
================================

- Author: Han Xiao (han.xiao@jina.ai)
- Jina VCS version: ``ece529e``
- Date: 24.02.2020

.. contents:: Table of Contents
   :depth: 2

Abstract
--------

Refactoring the :class:`jina.drivers.Driver` and its YAML config. Removing driver YAML config.


Rationale
---------

In the current implementation, the driver config is placed separately from the executor config. They are connected through CLI parameters ``--driver_yaml_path`` and ``--driver_group`` on the Pea’s level.

The poses multiple problems such as:

- As people working on executor, they have a very vague clue how it will work in the microservice/network settings. They later have to design the corresponding ``driver_group`` to match the logic of the executor.
- Almost every executor needs a driver, separating the driver from the executor seems unnecessary.
- Two YAML configs are cross-referencing the others. This is error-prone.

What we are expecting is the driver specification defined inside the executor YAML config, such as

.. highlight:: yaml
.. code-block:: yaml

    !CompoundExecutor
    components:
      - !NumpyIndexer
        with:
          num_dim: -1
          index_key: HNSW32
          index_filename: vec.idx
        metas:
          name: my_vec_indexer  # a customized name
          workspace: $TEST_WORKDIR
      - !MetaProtoIndexer
        with:
          index_filename: chunk.gzip
        metas:
          name: chunk_meta_indexer
          workspace: $TEST_WORKDIR
    metas:
      name: chunk_compound_indexer
      workspace: $TEST_WORKDIR
    on:
      SearchRequest:  # under request type1
        - name: my_vec_indexer
          method: query
          driver: chunk_search
        - name: chunk_meta_indexer
          method: meta_query
          driver: handlr_meta_search_chunk
      IndexRequest:    # under request type2
        - name: my_vec_indexer
          method: add
          driver: handler_chunk_index
        - driver: handler_prune_chunk
        - name: chunk_meta_indexer
          method: add
          driver: handler_meta_index_chunk


Specification
-------------


Adding ``requests.on`` syntax
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``requests`` field is defined at the same level with ``metas`` and ``with``. The ``on`` field describes what will the executor do on certain network requests. For example, for a :class:`jina.executors.encode.BaseEncoder`, which is expected to do :func:`encode` in any circumstances. The ``on`` field should be defined as follows:

.. highlight:: yaml
.. code-block:: yaml

    !AwesomeExecutor
    with:
    metas:
    requests:
        on:
            [SearchRequest, IndexRequest, TrainRequest]:
                - method: encode
                  driver: handler_encode_doc


.. confval:: requests.on.[RequestType]

    ``[RequestType]`` can be a list of ``jina.jina_pb2.Request``, i.e. SearchRequest, IndexRequest, TrainRequest and ControlRequest.

.. confval:: requests.on.[RequestType].method

    The executor's method to call, the method must be defined inside the scope of this executor. It is **optional** though.

.. confval:: requests.on.[RequestType].driver

    The corresponding driver to use, defined in :mod:`jina.drivers`. It is **always required**.

The ``on`` field supports multiple methods/drivers, and they are called in the order of how they defined. For example,

.. highlight:: yaml
.. code-block:: yaml

    on:
        SearchRequest:
            - driver: handler_prune_chunk
            - method: score
              driver: handler_chunk2doc_score
            - driver: handler_prune_doc


For the :mod:`jina.executors.compound.CompoundExecutor`, the ``on`` field supports specifying a method of a member executor with ``executor``. For example,

.. highlight:: yaml
.. code-block:: yaml

    !CompoundExecutor
    components:
      - !NumpyIndexer
        metas:
          name: my_vec_indexer  # a customized name
      - !MetaProtoIndexer
        metas:
          name: chunk_meta_indexer
    requests:
        on:
            SearchRequest:  # under request type1
                - executor: my_vec_indexer
                  method: query
                  driver: chunk_search
                - executor: chunk_meta_indexer
                  method: meta_query
                  driver: handler_meta_search_chunk

.. confval:: requests.on.[RequestType].executor

    The name of the sub-executor defined. It is only required for :class:`jina.executors.compound.CompoundExecutor`.

Note, a meaningful ``Executor`` is not always required. For example, a "router", which only forwards the message can be defined as the follows using simply the :class:`jina.executors.BaseExecutor`:

.. highlight:: yaml
.. code-block:: yaml

    !BaseExecutor
    requests:
      on:
        [SearchRequest, IndexRequest, TrainRequest]:
            - driver: handler_route


The default values on ``requests.on``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Certain behaviors are followed by all executors, it makes sense to have a :file:`requests.default.yml` to define all those default behaviors. A redefinition in the user-specified YAML will certainly override these default values.

.. confval:: requests.on.ControlRequest

    All executors must handle the ``ControlRequest`` correctly, so that they (and their container :class:`jina.peapods.pea.Pea`) can be closed/terminated gracefully. Therefore, it is more convenient to set ``ControlRequest`` as defaults:

    .. highlight:: yaml
    .. code-block:: yaml

        requests:
            on:
                ControlRequest:
                    - driver: handler_control_req


.. confval:: requests.pre and requests.post

    ``requests.pre`` defines how to handle the message before calling ``requests.on`, and ``requests.post`` defines how to handle the message after calling ``requests.on`. For example,

    .. highlight:: yaml
    .. code-block:: yaml

        requests:
            on:
                ControlRequest:
                    - driver: handler_control_req
            pre:
                - driver: hook_add_route_to_msg
            post:
                - driver: update_timestamp