# CRUD Operations

CRUD stands for Create, Read, Update, Delete. Together, they form the basis of any database engine. While Jina itself is *not* a database engine, it does provide these methods of interacting with the data stored in the indexers.

Until now, Jina has only supported indexing (creating) and querying (reading) documents. To update or delete a document, you'd have to edit your dataset, and then re-build the Flow and indexers. Needless to say, this could create problems if you had large datasets.

With the release of version `1.0` we're introducing **update** and **delete** operations. These are implemented across our executors and drivers and will allow you to update and delete documents by their ids. 

A basic example of this can be found in the `test_crud.py` file under `tests/integration/crud/simple`:

The Flow object now supports a `delete` and `update` method, with a signature similar to index:

```python
    with f:
        f.index(input_fn=random_docs(10))

    with f:
        f.update(input_fn=random_docs(10))

    with f:
        f.delete(input_fn=random_docs(10))
```

Note: deletion and update will happen by `id` of the document.

## Limitations

Unfortunately there are some limitations to what Jina can do for the moment. These were trade-offs we needed to implement to keep Jina performant, robust, and easy to use. Some of these will be addressed in future versions, while some are intrinsic to Jina's architecture.

1. **Partial update**

For the moment we do not support partial updates. So if you want to update a document, you need to send the entire document. This is due to Jina's architecture: the document is sent as one piece through the Flow.

1. **Update flows**

In the context of Flows with segmenters and chunks, a Document may end up being split into chunks. Currently, the Update request will not work for these. You will need to manually remove the chunks by their `ids`. Then you can remove the parent document as well, by its `id`. Finally, you can index the new document, with its new contents (and thus new, different child chunks).

1. **Sharding**

When sharding data in indexers, the data will be split across these. This is achieved due to the `polling: any` configuration. During a query, you will need to set `polling: all`. However, this will lead to some shards getting a query request with a key that doesn't exist. In this case, warnings will be emitted by the indexer. You can ignore these within this context. The warnings are there for the situations when missing keys are *not* expected.

1. **Indexing while querying**

The index, update, and delete operations cannot be executed within the same context as the query operation. This is due to the way flushing to disk works within the Flow and Executor context lifecycle. This is applicable across all VectorIndexers. Thus, you need to exit the Flow context when you want to switch from one set of operations to the other.

You can see this in the code listing in the beginning of this chapter.

1. **Expanding size**
   
The update and delete operations use a masking underneath. This is done to maintain high performance overall. However, this means that old data will not be deleted, but will simply be masked as being deleted. Thus the size on disk (and in memory) of the indexer will grow over time if you perform update or delete operations. We recommend you rebuild the indexers regularly. 

