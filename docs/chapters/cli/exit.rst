Gracefully Exit Jina
====================

In Python
---------

If you use ``with`` scope to start a Flow, then all resources (including Pods of all kinds) of the Flow will be released after your move out from the scope.

If you use :meth:`start` method to start the Flow, then you have to call :meth:`close` to shut down the Flow when you don't use it anymore.


In the Console
--------------

If you are running Jina locally (e.g. :command:`jina flow`), you can :kbd:`Control-c` or :kbd:`Command-c` to terminate it at any time. All :class:`BasePod` will receive this signal and shut down accordingly.

Container Pods and remote Pods sometimes take longer to shut down. When you open many replicas or many Pods, it may also take some time to release all resources.


Rule of thumb, for an individual Pod/Pea, when you see the following output from the console, then it is already shut down.

.. highlight:: bash
.. code-block:: bash

    BaseExecutor@7317[I]:no update since 2020-04-23 20:31:10, will not save. If you really want to save it, call "touch()" before "save()" to force saving
    BasePea@7317[I]:executor says there is nothing to save
    BasePea@7317[I]:msg_sent: 0 bytes_sent: 0 KB msg_recv: 0 bytes_recv:0 KB
    BasePea@7317[I]:msg_sent: 0 bytes_sent: 0 KB msg_recv: 0 bytes_recv:0 KB
    BasePea@7317[S]:terminated


For Flow, when you see the following output from the console, then it is shutdown already.

.. highlight:: bash
.. code-block:: bash

    chunk_idx-3@6376[S]:terminated
    chunk_idx-7@6383[I]:msg_sent: 653 bytes_sent: 590 KB msg_recv: 326 bytes_recv:956 KB
    chunk_idx-7@6383[S]:terminated
    chunk_idx-5@6378[I]:msg_sent: 653 bytes_sent: 587 KB msg_recv: 326 bytes_recv:948 KB
    chunk_idx-5@6378[S]:terminated
    chunk_idx-2@6375[I]:msg_sent: 651 bytes_sent: 583 KB msg_recv: 325 bytes_recv:939 KB
    chunk_idx-2@6375[S]:terminated
    chunk_idx-6@6381[I]:msg_sent: 653 bytes_sent: 589 KB msg_recv: 326 bytes_recv:953 KB
    chunk_idx-6@6381[S]:terminated
    Flow@6331[S]:flow is closed and all resources should be released already, current build level is EMPTY
