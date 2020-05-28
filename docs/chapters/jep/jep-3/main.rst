JEP 1 --- Adding support for multi-fields search
=================================================================

.. contents:: Table of Contents
   :depth: 3


:Author: Nan Wang (nan.wang@jina.ai)
:Created: May. 28, 2020
:Status: Proposal
:Related JEPs:
:Created on Jina VCS version: ``TBA``
:Merged to Jina VCS version: ``TBA``
:Released in Jina version: TBA
:Discussions: https://github.com/jina-ai/jina/issues/441

.. contents:: Table of Contents
   :depth: 2

Abstract
--------

[A short (~200 word) description of the technical issue being addressed.]

Motivation
---------
Multi-field search is commonly used in the production.
Concretely, the use case is to limit the query within some fields that the user has selected.
In the following case, there are three two fields in each document, i.e. ``title`` and ``summary``.
The use case is to query only from the ``title`` field. Given the query, ``q='painter'``,
the expected result is only ``hacker and painters``.

.. highlight:: json
.. code-block:: json
    {
      "id": 10,
      "title": "the story of the art",
      "summary": "This is a book about the history of the art, and the stories of the great painters"
    }, {
      "id": 11,
      "title": "hackers and painters",
      "summary": "This book discusses hacking, start-up companies, and many other technological issues"
    }


Rationale
---------
The core issue of this use case is the need of marking the ``Chunks`` from different fields.
During the query time, we would like to enable the users to change the selected fields in different queries without rebuilding the query ``Flow``.

.. highlight:: json
.. code-block:: json
    {
        "data": "painter",
        "top_k": 10,
        "mime_type": "application/text"
        "fields_name": ["title"],
    }

Flow
^^^^

.. image:: JEP3-index-design.png
   :align: center
   :width: 60%

To achieve this, we propose the following changes,

1. Add a new field in the protobuf defination of the ``Chunk``.

.. highlight:: proto
.. code-block:: proto
    message Chunk {
        ...
        string field_name = 13;
    }

2. Add a new ``Crafter`` for adding ``field_name`` information to the ``Chunk``.

.. highlight:: python
.. code-block:: python
    class FieldMapper(BaseSegmenter):
        def craft(self, *args, **kwargs) -> List[Dict]:
            pass

.. highlight:: python
.. code-block:: python
    class MapperDriver(SegmentDriver):
        pass

3. Add a new ``Driver`` for merging the messages defined by ``field_names`` in the request instead of merging all the messages defined by ``needs``.


4. Add a CompoundExecutor, namely ``FieldEncoder``, which wraps up ``FieldMapper`` and ``Encoder`` as a common pattern for multi-field search.

.. highlight:: yaml
.. code-block:: yaml
    !FieldEncoder
    on:
        SearchRequest, IndexRequest:
            - !MapperDriver:
                with:
                    executor: FieldMapper
            - !EncoderDriver
                with:
                    executor: TransformerTFEncoder


Specification
-------------

[Describe the syntax and semantics of any new feature.]

Backwards Compatibility
-----------------------

[Describe potential impact and severity on pre-existing code.]


Reference Implementation
------------------------

[Link to any existing implementation and details about its state, e.g. proof-of-concept.]

Open Issues
-----------

[Any points that are still being decided/discussed.]

References
----------

[A collection of URLs used as references through the JEP.]