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
    with:
      index_filename: doc.gzip
    metas:  # <- metas defined in :mod``
      name: doc_indexer  # a customized name
      workspace: $TEST_WORKDIR


.. confval:: !SomeExecutorClass

    The class of the executor, can be any class inherited from :mod:`jina.executors.BaseExecutor`. Note that it must starts with ``!`` to tell the YAML parser that the section below is describing this class.

.. confval:: with

    A list of arguments in the :func:`__init__` function of this executor. One can use environment variables here to expand the variables.

.. confval:: metas

    A list of meta arguments defined in :mod:`jina.executors.default`.


If an executor has no :func:`__init__` or :func:`__init__` requires no arguments, then one do not need to write ``with`` at all.

In the minimum case, if you don't want to specify any ``with`` and ``metas``, you can simply write:

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
      with:
        num_dim: -1
        index_key: HNSW32
        index_filename: vec.idx
      metas:
        name: my_vec_indexer
    - !MetaProtoIndexer
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


:class:`Flow` YAML Sytanx
---------------------------

:class:`jina.flow.Flow` can be loaded from a YAML config file. It follows the following syntax as the example below:

.. highlight:: yaml
.. code-block:: yaml

    !Flow
    with:
      driver_yaml_path:
      sse_logger: true
    pods:
      chunk_seg:
        driver: segment
        replicas: 3
      encode1:
        driver: index-meta-doc
        replicas: 2
        recv_from: chunk_seg
      encode2:
        driver: index-meta-doc
        replicas: 2
        recv_from: chunk_seg
      join_all:
        recv_from: [encode1, encode2]

A valid Flow specification starts with ``!Flow`` as the first line.

.. confval:: with

     A list of arguments in the :func:`jina.flow.Flow.__init__` function

.. confval:: pods

     A map of :class:`jina.peapods.pod.Pod` contained in the flow. The key is the name of this pod and the value is a map of arguments accepted by :command:`jina pod`. One can refer in ``send_to`` and ``recv_from`` to a pod by its name.

The flows given by the following Python code and the YAML config are identical.

.. highlight:: python
.. code-block:: python

    f = (Flow(driver_yaml_path='my-driver.yml')
         .add(name='chunk_seg', driver='segment',
              exec_yaml_path='preprocess/gif2chunk.yml',
              replicas=3)
         .add(name='doc_idx', driver='index-meta-doc',
              exec_yaml_path='index/doc.yml')
         .add(name='tf_encode', driver='encode',
              exec_yaml_path='encode/encode.yml',
              replicas=3, recv_from='chunk_seg')
         .add(name='chunk_idx', driver='index-chunk-and-meta',
              exec_yaml_path='index/npvec.yml')
         .join(['doc_idx', 'chunk_idx'])
         )

.. highlight:: yaml
.. code-block:: yaml

    !Flow  # my-flow.yml
    with:
      driver_yaml_path: my-driver.yml
    pods:
      chunk_seg:
        driver: segment
        exec_yaml_path: preprocess/gif2chunk.yml
        replicas: 3
      doc_idx:
        driver: index-meta-doc
        exec_yaml_path: index/doc.yml
      tf_encode:
        driver: encode
        exec_yaml_path: encode/encode.yml
        recv_from: chunk_seg
        replicas: 3
      chunk_idx:
        driver: index-chunk-and-meta
        exec_yaml_path: index/npvec.yml
      join_all:
        driver: merge
        recv_from: [doc_idx, chunk_idx]

.. highlight:: python
.. code-block:: python

    from jina.flow import Flow
    g = Flow.load_config('my-flow.yml')

    assert(f==g)  # return True

Note that you can replace the value of ``replicas`` with an environment variables ``$REPLICAS`` in the YAML and it will be expanded during :func:`load_config`.