:class:`Executor` YAML Syntax
==============================

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

