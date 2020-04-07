OS Environment Variables Used in Jina
=====================================




Here is the list of environment variables that ``jina`` respects during runtime.

.. note::
    These enviroment variables must be set **before** starting ``jina`` or before any ``import jina`` in Python. Changing the variables while ``jina`` is running may result in unexpected result and exceptions.

.. confval:: JINA_PROFILING

    Set to any non-empty value to turn on service-level time profiling for JINA.

    :default: unset


.. confval:: JINA_WARN_UNNAMED

    Set to any non-empty value to turn on the warning for unnamed executors.

    :default: unset

.. confval:: JINA_VCS_VERSION

    Git version of ``jina``. This is used when ``--check-version`` is turned on. For official docker image of ``jina``, ``JINA_VCS_VERSION`` is automatically set to the git version during the building procedure.

    :default: the git head version for ``jina`` image. If you are using ``jina`` locally outside docker container then this is unset.

.. confval:: JINA_CONTROL_PORT

    Control port of all pods.

    :default: unset. A random port will be used for each :func:`BasePod`.


.. confval:: JINA_CONTRIB_MODULE

    Paths of the third party components.

    :default: unset

.. confval:: JINA_IPC_SOCK_TMP

    Temp directory when using IPC sockets for the control port, not used on Windows system or when the control port is over TCP sockets.

.. confval:: JINA_LOG_FILE

    Control where the logs output to. Possible values: ``TXT`` for plain text format, which is the uncolored version of the screen output. ```JSON`` for structured log output.

    :default: unset, aka stdout only.

.. confval:: JINA_SOCKET_HWM

    High-watermarks of ZMQ send & receive sockets. Reference: http://api.zeromq.org/master:zmq-setsockopt

    :default: 4

.. confval:: JINA_ARRAY_QUANT

    Quantization scheme when storing ndarray into protobuf message, useful for reducing the network latency and saving bandwidth. Possible values: ``fp16`` (almost lossless), ``uint8``.

    :default: unset

.. confval:: JINA_LOG_NO_COLOR

    Show colored logs in stdout, set to any non-empty value to disable the color log, e.g. if you want to pipe the log into other apps.

    :default: unset

.. confval:: JINA_EXECUTOR_WORKDIR

    The default executor working directory, where dumping and IO output happens.

    :default: unset

.. confval:: JINA_LOG_VERBOSITY

    The log verbosity of the Jina logger. Possible values are ``DEBUG``, ``WARNING``, ``INFO``, ``ERROR``, ``CRITICAL``.

    :default: ``INFO``


.. confval:: JINA_LOG_LONG

    When set, the filename, function name and line number will be displayed as well.

    :default: unset

.. confval:: JINA_DEFAULT_HOST

    The default host address of Jina.

    :default: `0.0.0.0`

.. confval:: JINA_TEST_CONTAINER

    If set, then all container-related tests will be conducted in the unit test.

    :default: unset

.. confval:: JINA_TEST_PRETRAINED

    If set, then all pretrained model-related tests will be conducted in the unit test.

    :default: unset
