Jina YAML Syntax Reference
==========================



Jina configurations use YAML syntax, and must have either a ``.yml`` or ``.yaml`` file extension. If you're new to YAML and want to learn more, see `Learn YAML in five minutes. <https://www.codeproject.com/Articles/1214409/Learn-YAML-in-five-minutes>`_

:class:`Executor` YAML Syntax
-----------------------------

All executors defined in :mod:`jina.executors` can be loaded from a YAML config via :func:`jina.executors.BaseExecutor.load_config` or via the CLI :command:`jina pod --uses`.

The executor YAML config follows the syntax below.

.. highlight:: yaml
.. code-block:: yaml

    !BasePbIndexer
    with:
      index_filename: doc.gzip
    metas:  # <- metas defined in :mod`jina.executors.metas`
      name: doc_indexer  # a customized name
      workspace: $TEST_WORKDIR


.. confval:: !SomeExecutorClass

    The class of the executor, can be any class inherited from :mod:`jina.executors.BaseExecutor`. Note that it must starts with ``!`` to tell the YAML parser that the section below is describing this class.

.. confval:: with

    A list of arguments in the :func:`__init__` function of this executor. One can use environment variables here to expand the variables.

.. confval:: metas

    A list of meta arguments defined in :mod:`jina.executors.metas`.


If an executor has no :func:`__init__` or :func:`__init__` requires no arguments, then one do not need to write ``with`` at all.

In the minimum case, if you don't want to specify any ``with`` and ``metas``, you can simply write:

.. highlight:: yaml
.. code-block:: yaml

    # encoder.yml
    !AwesomeExecutor

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


Referencing Variables in :class:`Executor` and :class:`CompoundExecutor` YAML
-----------------------------------------------------------------------------

In the YAML config, one can reference environment variables with ``$ENV``, or using ``{path.variable}`` to reference the variable defined inside the YAML. For example,

.. highlight:: yaml
.. code-block:: yaml

    components:
      - with:
          index_filename: metaproto
        metas:
          name: test_meta
          good_var:
            - 1
            - 2
          bad_var: '{root.metas.name}'
      - with:
          index_filename: npidx
        metas:
          name: test_numpy
          bad_var: '{root.components[0].metas.good_var[1]}'  # expand to the string 'real-compound'
          float_var: '{root.float.val}'  # expand to the float 0.232
          mixed: '{root.float.val}-{root.components[0].metas.good_var[1]}-{root.metas.name}'  # expand to the string '0.232-2-real-compound'
          mixed_env: '{root.float.val}-$ENV1'  # expand to the string '0.232-a'
          name_shortcut: '{this.name}'  # expand to the string 'test_nunpy'
    metas:
      name: real-compound
    rootvar: 123
    float:
      val: 0.232

.. confval:: root.var

    Referring to the top-level variable defined in the root.

.. confval:: this.var

    Referring to the same-level variable.

.. note::
    One must quote the string when using referenced values, i.e. ``'{root.metas.name}'`` but not ``{root.metas.name}``.



:class:`Driver` YAML Sytanx
---------------------------

:class:`jina.drivers.Driver` helps the :mod:`jina.executors` to handle the network traffic by interpreting the traffic data (e.g. Protobuf) into the format that the Executor can understand and handle (e.g. Numpy array). Drivers can be specified using keyword `requests` and `on`

.. highlight:: yaml
.. code-block:: yaml

    !CompoundExecutor
    components:
      - !Splitter
        metas:
          name: splitter
      - !Sentencizer
        with:
          min_sent_len: 3
          max_sent_len: 128
          punct_chars: '.,;!?:'
        metas:
          name: sentencizer
    name: crafter
    workspace: $WORKSPACE
    metas:
      py_modules: splitter.py
    requests:
      on:
        [SearchRequest, IndexRequest]:
          - !CraftDriver
            with:
              executor: splitter
              method: craft
          - !SegmentDriver
            with:
              executor: sentencizer
        ControlRequest:
          - !ControlReqDriver {}


.. confval:: requests

    .. confval:: on

        .. confval:: request_type

            Possible values are ``QueryRequest``, ``IndexRequest``, ``TrainRequest``, or a list of them.

            .. confval:: !SomeDriverClass

                The class of the driver, can be any class inherited from jina.drivers.BaseDriver. Note that it must starts with ! to tell the YAML parser that the section below is describing this class.

            .. confval:: with

                A list of arguments in the :func:`__init__` function of this driver. One can use environment variables here to expand the variables.

            .. confval:: metas

                A list of meta arguments defined in :mod:`jina.executors.metas`.

.. note::
    If no drivers are specified in the yaml file, default drivers defined in `executors.requests.*` files at :mod:`jina.resources` wii be used.

:class:`Flow` YAML Sytanx
---------------------------

:class:`jina.flow.Flow` can be loaded from a YAML config file. It follows the following syntax as the example below:

.. highlight:: yaml
.. code-block:: yaml

    !Flow
    with:
      sse_logger: true
    pods:
      chunk_seg:
        driver_group: segment
        replicas: 3
      encode1:
        driver_group: index-meta-doc
        replicas: 2
        needs: chunk_seg
      encode2:
        driver_group: index-meta-doc
        replicas: 2
        needs: chunk_seg
      join_all:
        needs: [encode1, encode2]

A valid Flow specification starts with ``!Flow`` as the first line.

.. confval:: with

     A list of arguments in the :func:`jina.flow.Flow.__init__` function

.. confval:: pods

     A map of :class:`jina.peapods.pod.BasePod` contained in the flow. The key is the name of this pod and the value is a map of arguments accepted by :command:`jina pod`. One can refer ``needs`` to a pod by its name.

The flows given by the following Python code and the YAML config are identical.

.. highlight:: python
.. code-block:: python

    f = (Flow(uses='my-driver.yml')
         .add(name='chunk_seg', driver_group='segment',
              uses='preprocess/gif2chunk.yml',
              replicas=3)
         .add(name='doc_idx', driver_group='index-meta-doc',
              uses='index/doc.yml')
         .add(name='tf_encode', driver_group='encode',
              uses='encode/encode.yml',
              replicas=3, needs='chunk_seg')
         .add(name='chunk_idx', driver_group='index-chunk-and-meta',
              uses='index/npvec.yml')
         .join(['doc_idx', 'chunk_idx'])
         )

.. highlight:: yaml
.. code-block:: yaml

    !Flow  # my-flow.yml
    with:
      driver_uses: my-driver.yml
    pods:
      chunk_seg:
        driver_group: segment
        exec_uses: preprocess/gif2chunk.yml
        replicas: 3
      doc_idx:
        driver_group: index-meta-doc
        exec_uses: index/doc.yml
      tf_encode:
        driver_group: encode
        exec_uses: encode/encode.yml
        needs: chunk_seg
        replicas: 3
      chunk_idx:
        driver_group: index-chunk-and-meta
        exec_uses: index/npvec.yml
      join_all:
        driver_group: merge
        needs: [doc_idx, chunk_idx]

.. highlight:: python
.. code-block:: python

    from jina.flow import Flow
    g = Flow.load_config('my-flow.yml')

    assert(f==g)  # return True

Note that you can replace the value of ``replicas`` with an environment variables ``$REPLICAS`` in the YAML and it will be expanded during :func:`load_config`.