:class:`Driver` YAML Syntax
============================

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
