# CRUD Operations in Jina

Paragraph. CRUD in general.

<!-- Paragraph. Limitations until this point: only index and search. Incremental indexing. ) -->

Up until this point Jina only supported indexing (creating) and querying (reading) documents. In order to update or delete a document, you'd have to edit your dataset, and then re-build the Flow and the indexers. Needless to say, this can create problems if you have large datasets.

<!-- What are we doing now? Update, delete. -->
With the release of version X.X.X we are introducing **update** and **delete** operations. These are implemented across our indexers and drivers. This will allow you to update and delete documents by their ids. 


```python
# TODO code sample of Flow, or Index, with update, delete
```

## Limitations

Unfortunately there are some limitations to what Jina can do for the moment. These were trade-offs we needed to implement in order to keep Jina performant, robust, and easy to use. We are working on handling these too.

1. **Partial update**

    For the moment we do not support partial updates. That means that if you want to update a document, you need to send the entire document. A partial update would allow you to only send a specific field, or part of the document.

1. **Update flows**

   In the context of flows with segmenters and chunkers, a Document may end up being split into chunks. Currently, the Update request will not work for these. You can still perform a replace operation, by first deleting the document (which will delete its chunks) and then adding the new version.

1. **Sharding, replicas**

   <!-- TODO -->
    This is not handled yet.

1. **Advanced Indexers**

    `Faiss` & `Annoy` indexers don't support update while querying. Indexers need to be re-loaded. Same for the `BinaryPbIndexer`.

   ```python
   # TODO code example
   ```

1. **Expanding size** 

   The update and delete operations use a masking underneath. This is done in order to maintain high performance overall. However, this means that old data will not be deleted, but will simply be masked as being deleted. Thus the size on disk (and in memory) of the indexer will grow with time if you perform update or delete operations. We recommend you rebuild the indexers regularly. 

