Prevent Indexing Duplicates
---------------------------

When indexing documents, it is common to have duplicate documents received by the search system. One can either remove the duplicates before sending the duplicates to Jina or leave it to Jina for handling the duplicates.

To prevent indexing duplicates, one needs to add ``_unique`` for the ``uses_before`` option. For example,

.. confval:: Python API


    .. highlight:: python
    .. code-block:: python

        from jina.flow import Flow
        from jina.proto import jina_pb2

        doc_0 = jina_pb2.Document()
        doc_0.text = f'I am doc0'
        doc_1 = jina_pb2.Document()
        doc_1.text = f'I am doc1'

        def assert_num_docs(rsp, num_docs):
            assert len(rsp.IndexRequest.docs) == num_docs

        f = Flow().add(
            uses='NumpyIndexer', uses_before='_unique')

        with f:
            f.index(
                [doc_0, doc_0, doc_1],
                output_fn=lambda rsp: assert_num_docs(rsp, num_docs=2))

Under the hood, the configuration yaml file, :file:``executors._unique.yml``, under the :file:``jina/resrouces`` is used. The yaml file is defined as below


.. confval:: YAML spec

    .. highlight:: yaml
    .. code-block:: yaml

        !DocIDCache
        with:
          index_path: cache.tmp
        requests:
          on:
            [SearchRequest, TrainRequest, IndexRequest, ControlRequest]:
              - !RouteDriver {}
            IndexRequest:
              - !TaggingCacheDriver
                with:
                  tags:
                    is_indexed: true
              - !FilterQL
                with:
                  lookups: {tags__is_indexed__neq: true}


:class:`jina.executors.indexers.cache.DocIdCache` uses document ID to detect the duplicates. The documents with the same ID are considered as the same one. :class:`jina.drivers.cache.TaggingCacheDriver` keep a set of the indexed keys and check against the cache for a hit. If the document id exists, :class:`jina.drivers.cache.TaggingCacheDriver` sets the customized keys in the `tags` field to the predefined value. In the above configuration, ``is_indexed`` in the ``tags`` field is set to ``true`` when the document id hit the cached indexed keys. Afterwards, :class:`jina.drivers.querylang.filter.FilterQL` is used to filter out the duplicate documents from the request.


In Jina, the document ID is by default generated a new hexdigest based on the content of the document. The hexdigest is calcuated with `blake2b algorithm <https://docs.python.org/3.7/library/hashlib.html#hashlib.blake2b>`_. By setting ``override_doc_id=True``, users can also use customized document ids with Jina client and add ``tags`` to map to their unique concepts.

.. warning::
    When setting ``override_doc_id=True``, a customized id is only acceptable if

    - it is a `hexadecimal <https://en.wikipedia.org/wiki/Hexadecimal>`_ string

    - it has an even length


