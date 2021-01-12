:class:`Flow` YAML Syntax
==========================

:class:`jina.Flow` can be loaded from a YAML config file. It follows the following syntax as the example below:

.. highlight:: yaml
.. code-block:: yaml

    !Flow
    version: '1.0'
    with:
        restful: true
    pods:
      - name: pod0  # notice the change here, name is now an attribute
        method: add  # by default method is always add, available: add, needs, inspect
        uses: _pass
        needs: gateway
      - name: pod1  # notice the change here, name is now an attribute
        method: add  # by default method is always add, available: add, needs, inspect
        uses: _pass
        needs: gateway
      - method: inspect  # add an inspect node on pod1
      - method: needs  # let's try something new in Flow YAML v1: needs
        needs: [pod1, pod0]

A valid Flow specification starts with ``!Flow`` as the first line.


.. confval:: version

     The version number string of Flow YAML schema.

     .. warning::
        Don't forget to quote your version number, it must be a string.


.. confval:: with

     A list of arguments in the :func:`jina.Flow.__init__` function. Check :command:`jina flow --help` for details. Extra ``kwargs`` will be passed to **all** pods as the common ``kwargs``.

.. confval:: pods

     The list of :class:`jina.peapods.Pod` contained in the flow. The key is the name of this pod and the value is a map of arguments accepted by :command:`jina pod --help`. Besides those ``kwargs``, there are some optional fields one can set:

.. confval:: pods[*].name

    The user defined name of the Pod. Optional. When not given, it will named as ``pod0``, ``pod1``, etc.

.. confval:: pods[*].method

    The method for appending this Pod into the Flow. Optional, by default it's ``add``:

        - ``add``: same as ``Flow.add(...)``
        - ``needs``: same as ``Flow.needs(...)``
        - ``inspect``: same as ``Flow.inspect(...)``

.. confval:: pods[*].needs

    Identifies any Pods that must complete successfully before this Pod will run. It can be a string or array of strings. By default, ``needs`` always contains the previous Pod, unless written in other way. ``needs`` can be used to create intra-Pod parallelization. For example, the Flow below runs ``pod2`` and ``pod3`` in parallel:

    .. highlight:: yaml
    .. code-block:: yaml

        !Flow
        version: '1.0'
        pods:
            - name: pod1
            - name: pod2
            - name: pod3
              needs: pod1
            - name: pod4
              needs: [pod2, pod3]




