Jina YAML Reference
===================

Jina configurations use YAML syntax, and must have either a ``.yml`` or ``.yaml`` file extension. If you're new to YAML and want to learn more, see `Learn YAML in five minutes. <https://www.codeproject.com/Articles/1214409/Learn-YAML-in-five-minutes>`_

:class:`Executor` YAML Syntax
-----------------------------

All executors defined in :mod:`jina.executors` can be loaded from a YAML config via :func:`jina.executors.BaseExecutor.load_config` or via the CLI :command:`jina pod --exec_yaml_path`.

The executor YAML config follows the syntax below.

.. highlight:: yaml
.. code-block:: yaml

    !MetaProtoIndexer
    specs:
      data_path: $TEST_WORKDIR/doc.gzip
    metas:  # <- metas defined in :mod``
      name: doc_indexer  # a customized name
      work_dir: $TEST_WORKDIR

.. confval:: !SomeExecutorClass

    The class of the executor, can be any class inherited from :mod:`jina.executors.BaseExecutor`. Note that it must starts with ``!`` to tell the YAML parser that the section below is describing this class.

.. confval:: specs

    A list of arguments in the :func:`__init__` function of this executor. One can use environment variables here to expand the variables.

.. confval:: metas

    A list of meta arguments defined in :mod:`jina.executors.default`.


If an executor has no :func:`__init__` or :func:`__init__` requires no arguments, then one do not need to write ``specs`` at all.

In the minimum case, if you don't want to specify any ``specs`` and ``metas``, you can simply write:

.. highlight:: yaml
.. code-block:: yaml

    # encoder.yml
    !AwesomeExecutor {}

Or even not using this YAML but simply write:

.. highlight:: python
.. code-block:: python

    import jina.executors.BaseExecutor

    a = BaseExecutor.load_config('AwesomeExecutor')


:class:`CompoundExecutor` YAML Syntax
--------------------------------------------

A compound executor is a set of executors bundled together, as defined in :mod:`jina.executors.compound`. It follows the syntax above with an additional feature: `routing`.

.. highlight:: yaml
.. code-block:: yaml

    !CompoundExecutor
    components:
    - !NumpyIndexer
      specs:
        num_dim: -1
        index_key: HNSW32
        data_path: $TEST_WORKDIR/vec.idx
      metas:
        name: my_vec_indexer
    - !MetaProtoIndexer
      specs:
        data_path: $TEST_WORKDIR/chunk.gzip
      metas:
        name: chunk_meta_indexer
    specs:
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
      work_dir: $TEST_WORKDIR

.. confval:: components

    A list of executors specified. Note that ``metas.name`` must be specified if you want to later quote this executor in ``specs.routes``.

.. confval:: specs

    .. confval:: routes

        .. highlight:: yaml
        .. code-block:: yaml

            A:
                B: C

        It defines a function mapping so that a `new` function :func:`A` is created for this compound executor and points to :func:`B.C`. Note that ``B`` must be a valid name defined in ``components.metas.name``


:class:`Driver` YAML Sytanx
---------------------------

:class:`jina.drivers.Driver` connects :class:`jina.peapods.pea.Pod` and :mod:`jina.executors`. A driver map is a collection of drivers which can be referred by the Pod via CLI (``jina pod --driver_yaml_path --driver``).

.. highlight:: yaml
.. code-block:: yaml

    drivers:
      encode:
        handlers:
          /:
            - handler_encode_doc: encode

      segment:
        handlers:
          /:
            - handler_segment: transform

      index-chunk-and-meta:
        handlers:
          QueryRequest:
            - handler_chunk_search: query
            - handler_meta_search_chunk: meta_query
          IndexRequest:
            - handler_chunk_index: add
            - handler_prune_chunk
            - handler_meta_index_chunk: meta_add


.. confval:: drivers

    A map of the names to the handlers, the name can be referred in ``jina pod --driver``

.. confval:: handlers

    A map of request types to a list of handlers

    .. highlight:: yaml
    .. code-block:: yaml

        request_type:
            - handler: executor_func

    .. confval:: request_type

        Possible values are ``QueryRequest``, ``IndexRequest``, ``TrainRequest`` and ``/`` representing all requests.

    .. confval:: handler

        All handler functions defined in :mod:`jina.drivers.handlers`

    .. confval:: (optional) executor_func

        If the handler is paired with certain executor function, then here should be the name of it