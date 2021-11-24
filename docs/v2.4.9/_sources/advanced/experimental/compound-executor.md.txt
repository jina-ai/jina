(compound-executor)=

# Compound Executors

A "Compound" Executor is a special pattern of composing Executor. It glues multiple Executors into one Executor class.
This allows developers to leverage the feature of multiple Executors while keeping their original implementations *as-is*.

Here are some examples in practice:

- combining a Storage and a Search Indexer in one, for easier access, scaling etc.;
- combining a custom ranker and an Indexer in one, for cases where `top_k` is not achieved after a ranking process
  filters out results;
- having Indexers that store multiple level of granularity in one Executor, for easier lookup and custom logic.

A Compound Executor can be also seen as a monolith counterpart of the microservice design. A Compound Executor,
regardless how many sub-Executors it contains, is normally **located in one process**; hence it can only be scaled in/out jointly.

## Example

In this example, I will show you how to build a Compound Indexer. I will combine a Storage Indexer and a Searcher Indexer
into one Executor class.

First, I follow the guide to create a new Executor, using `jina hub new`. See {ref}`here <create-hub-executor>` for more
info. Then, I copy the classes [`MongoStorage`](https://hub.jina.ai/executor/3e1sp6fp)
and [`AnnoySearcher`](https://hub.jina.ai/executor/wiu040h9) from their respective repositories.

```{caution}
If you want to develop a Compound Executor based on existing Executors in Jina Hub, 
you have to copy-paste the code of the classes into your own Executor's package, like what I did below.

This is not recommended practice in Python. This is because, for now, the Executors in Jina Hub can **not** be imported as Python modules.

It is, however, outside the scope of this tutorial, to show you how to organize a Python module. Do as you see fit.
```

```python
from jina import Executor, requests, DocumentArray


class MongoDBStorage(Executor):
    ...  # copied from https://hub.jina.ai/executor/3e1sp6fp


class AnnoySearcher(Executor):
    ...  # copied from https://hub.jina.ai/executor/wiu040h9


class CompoundExecutor(Executor):
    def __init__(self, **kwargs):  # you args go here
        super().__init__(**kwargs)  # you still need to initialize the base class, Executor
        self._storage = MongoDBStorage(**kwargs)  # other args could be passed here
        self._vector_searcher = AnnoySearcher(**kwargs)  # same

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):  # we combine the logic in one place
        results = self._vector_searcher.search(docs, **kwargs)
        # here you would put any other custom logic you have
        return self._storage.search(results, **kwargs)
```

You can then continue adding custom endpoints as you want.

The usage of `CompoundExecutor` is no different from the normal Executor.