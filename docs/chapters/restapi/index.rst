Jina REST API Specification
===========================

.. note::
    To use REST API support, you need to install jina via :command:`pip install "jina[http]"` or use the corresponding feature-enabled Docker image.

Interface
---------

POST an IndexRequest
~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   # POST an IndexRequest to `http://0.0.0.0:5555/api/index`

   curl -X POST -d '{"first_doc_id": 5, "data": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC", "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC"]}
   ' -v -i 'http://0.0.0.0:5555/api/index'

POST a SearchRequest
~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   # POST an SearchRequest to `http://0.0.0.0:5555/api/index`

   curl -X POST -d '{"top_k": 5, "data": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC", "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC"]}
   ' -v -i 'http://0.0.0.0:5555/api/search'

Remarks on POST :command:`:<port_expose>/api/<mode>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``<mode>`` should be one of ``index``, ``train`` and ``search``
-  MIME type should be ``application/json``
-  the content should at least have the ``data`` field, which contains a
   list of data URI, each corresponds to one document.
-  You can specify other arguments in the request. For example,
   ``top_k``, ``batch_size``, ``first_doc_id``. The full list can be
   `found in here <../cli/jina-client.html#client-specific%20arguments>`_. Please note that not all arguments are supported on
   the REST API level at the moment.
-  The REST endpoint will be served at ``port_expose``

Switching from gRPC gateway to REST gateway
-------------------------------------------

By default Jina uses gRPC as the gateway for receiving and sending
requests from and to clients. Some users especially the frontend
engineers may look for a RESTful API to communicate with Jina. This can
be done by easily.

In Python API
~~~~~~~~~~~~~

.. code:: python

   from jina.flow import Flow

   f = (Flow(rest_api=True).add(...)
                           .add(...))

Note that you can not use ``f.index``, ``f.search`` and ``f.train`` here
anymore. These IO interface are based on Python client, which uses gRPC
behind the scene. You should use Javascript or Node and send HTTP
request to communicate with this Flow instead.

To block a Flow, use ``block()``

.. code:: python

   with f:
       f.block()

In YAML
~~~~~~~

.. code:: yaml

   !Flow
   with:
       rest_api: true

And then either load it in Python via ``Flow.load_config('my.yml')`` or
via CLI: ``jina flow --yaml-path my.yml``

In gateway's CLI (advanced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most of the cases you just need to set ``rest-api`` on the Flow level.
But in case you need to start a separate gateway with ``rest_api``
enabled. You can do:

.. code:: bash

   jina gateway --rest-api

Unsupported Features in REST API
--------------------------------

In the current version, the following features are only supported by
gRPC interface not by REST API. We are continuously improving it.

-  ``in_proto`` is not supported. You can not send raw binary Protobuf
   documents to Jina using REST API interface.
-  ``callback_on_body`` is not supported.
-  ``batch_size`` is not supported. As it will break one request into
   multiple responses.
-  REST gateway does not do prefetching. There will be no bi-directional streaming. Internally, REST gateway communicate with Pod in async way, this is the same as in gRPC gateway. However, only after *all* results are finished, will the REST gateway return the results. This is different than the gRPC gateway, where the results are streamed in an async way.
-  Please pay attention to the case transformation on the keys in the JSON payload returned. `doc_id` defined in gRPC protobuf will be returned as `docId` in JSON.
