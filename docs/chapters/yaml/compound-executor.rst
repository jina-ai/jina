:class:`CompoundExecutor` YAML Syntax
=====================================

A compound executor is a set of executors bundled together, as defined in :mod:`jina.executors.compound`. It follows the syntax above with an additional feature: `routing`.

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
        name: my_vec_indexer
    - !BasePbIndexer
      with:
        index_filename: chunk.gzip
      metas:
        name: chunk_meta_indexer
    with:
      routes:
        meta_add:
          chunk_meta_indexer: add
        meta_query:
          chunk_meta_indexer: query
        query:
          my_vec_indexer: query
        add:
          my_vec_indexer: add
    metas:
      name: chunk_compound_indexer
      workspace: $TEST_WORKDIR

.. confval:: components

    A list of executors specified. Note that ``metas.name`` must be specified if you want to later quote this executor in ``with.routes``.

.. confval:: with

    .. confval:: routes

        .. highlight:: yaml
        .. code-block:: yaml

            A:
                B: C

        It defines a function mapping so that a new function :func:`A` is created for this compound executor and points to :func:`B.C`. Note that ``B`` must be a valid name defined in ``components.metas.name``

