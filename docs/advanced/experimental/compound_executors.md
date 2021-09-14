(compound-executor)=
# Compound Executors

A Compound Executor is an advanced type of Executor. 
This combines two or more Executors into one class, in order to facilitate special logic.
Examples of this include:

- combining a Storage and a Search Indexer in one, for easier access, scaling etc.
- combining a custom ranker and an Indexer in one, for cases where `top_k` is not achieved after a ranking process filters out results
- having Indexers that store multiple level of granularity in one Executor, for easier lookup and custom logic

If you want to develop a `CompoundExecutor`-type Executor based on one of the Executors existing in Jina Hub, you have to copy-paste the code of the classes you need into your own Executor's package.
This is because, for now, the Executors in Jina Hub can **not** be imported as Python modules.

## Example

In this short example I will show you how this can be done. 
I will combine a Storage Indexer and a Searcher Indexer in one class.
I will trim the copied code.

First, I follow the guide to create a new Executor, using `jina hub new`. See {ref}`here <create-hub-executor>` for more info.
Then, I copy the classes [`MongoStorage`](https://hub.jina.ai/executor/3e1sp6fp) and [`AnnoySearcher`](https://hub.jina.ai/executor/wiu040h9) from their respective repositories.
In this example, I will keep all the code in one large file. 
This is not recommended practice in Python.
It is, however, outside the scope of this tutorial, to show you how to organize a Python module.
Do as you see fit.

```python
from jina import Executor, requests, DocumentArray

class MongoDBStorage(Executor):
    ...

class AnnoySearcher(Executor):
    ...

class MyExecutor(Executor):
    def __init__(self, ..., **kwargs): # you args go here
        super().__init__(**kwargs)  # you still need to initialize the base class, Executor
        self._storage = MongoDBStorage(**kwargs) # other args could be passed here
        self._vector_searcher = AnnoySearcher(**kwargs) # same
        ... # other constructor logic

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs): # we combine the logic in one place
        results = self._vector_searcher.search(docs, **kwargs)
        # here you would put any other custom logic you have
        docs = self._storage.search(results, **kwargs)
        
    # you can then continue adding custom logic endpoints
    # e.g. importing from MongoDB into the vector searcher
```
