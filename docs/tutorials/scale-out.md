# Executor Scale-Out With Replicas & Shards

```{article-info}
:author: Bo @ Jina AI
:date: February 8, 2022
```

## Overview

A typical Jina `Flow` orchestrates multiple `Executors`.
By default, a Jina `Executor` runs with a single `Replica` and `Shard`.
Some `Executor` in the Flow might be less performant than other `Executors`,
this could be a performance bottleneck when you deploy your Jina service to the production environment 

Luckily, Jina `Flow` allows you to config the number of `Replicas` and `Shards`.
`Replica` is used to increase `Executor` throughput and availability.
`Shard` is used for data partitioning.
In this tutorial, we'll dive into these two concepts and see how you can make use of `Replica` and `Shard` to scale out your `Executor`.

## Before you start
<!-- Delete this section if your readers can go to the steps without requiring any prerequisite knowledge. -->
Before you begin, make sure you meet these prerequisites:

* You have a good understanding of Jina [Flow](../fundamentals/flow/index.md).
* You have a good understanding of Jina [Executor](../fundamentals/executor/index.md)
* Please install the following dependencies if you haven't:


```shell
pip install jina
pip install sklearn
```

## Speed-Up A Slow Executor: Replicas

### Context

Imagine you are building a text-based search system and you have an `Executor` to transform text to its [tf-idf](https://en.wikipedia.org/wiki/Tf-idf) vector representation.
This could become a performance bottleneck to your search system.
The Executor looks like this:

```python
from jina import Executor, requests
from sklearn.feature_extraction.text import TfidfVectorizer

class MyTokenizer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vectorizer = TfidfVectorizer()
    
    @requests
    def vectorize(self, docs, **kwargs):
        # Extract all text from jina document and feed into sklearn
        X = self.vectorizer.fit_transform(docs.contents)
        # Assign results as document embeddings
        docs.embeddings = X
```

And we create a `Flow` and make use a text corpus from scikit-learn to use this `Executor`:

```python
from jina import Flow
from docarray import Document
from sklearn.datasets import fetch_20newsgroups

f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyTokenizer)

data, _ = fetch_20newsgroups(
    shuffle=True,
    random_state=1,
    return_X_y=True,
)

def news_generator():
    for item in data:
        yield Document(text=item)
```

### Scale-Up an Executor

When you start your `Flow`, you might discover to process all the text corpus, this process takes a while:

```python
with f:
    results_da = f.post('/foo', news_generator, show_progress=True)
```

As Jina reported, it takes around 6 seconds to accomplish the task.
6 seconds sounds reasonable (at index time), but bear in mind that this is just a test corpus.
What if you need to index millions of documents?

```shell
           Flow@2011375[I]:🎉 Flow is ready to use!                                        
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:52775
	🔒 Private network:	172.31.29.177:52775
	🌐 Public address:	54.93.57.58:52775
⠇       DONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━ 0:00:06 18.1 step/s . 115 steps done in 6 seconds
```

Jina allows you to scale your `Executor` very easily, with only one parameter change:

```diff
+ f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyTokenizer, replicas=2)
- f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyTokenizer)
```

Let's see how it performs given 2 `Replicas`:

```shell
           Flow@2011375[I]:🎉 Flow is ready to use!                                        
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:57040
	🔒 Private network:	172.31.29.177:57040
	🌐 Public address:	54.93.57.58:57040
⠇       DONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━ 0:00:03 37.0 step/s . 115 steps done in 3 seconds
```

As you can see, now it only takes 3 seconds to finish the task.
Quite intuitive, right? In a later section,
we'll introduce what `replicas` means under different deployment options.

## Split Data into Partitions

### Context

Now with your text corpus encoded as TF-IDF embeddings,
it's time to save the results.
We'll use Jina's [PQLiteIndexer](https://hub.jina.ai/executor/pn1qofsj) to persist our embeddings for fast Approximate Nearest Neighbor Search.

And you add this `PQLiteIndexer` to your Flow:

```python
from jina import Flow

f = Flow().add(
    name='fast_executor').add(
    name='slow_executor', uses=MyTokenizer).add(
    name='pqlite_executor', uses='jinahub://PQLiteIndexer', uses_with={
      'dim': 5215,
      'metric': 'cosine'
    },
    uses_metas={'workspace': 'CHANGE-TO-YOUR-PATH/workspace'},
    install_requirements=True)
```

### Partitioning the Data

Now let's run the `Flow` to index your data:
```python
with f:
    f.post(on='/index', inputs=news_generator, show_progress=True)
```

The `PQLiteIndexer` will save your indexed `Documents` to your specified `workspace` (directory).
Since the default number of shards is one.
All the data will be saved to `YOUR-WORKSPACE-DIR/PQLiteIndexer/0/` where `0` is the shard id.

If you want to distribute your data to different places, Jina allows you to use `shards` to specify the number of shards.

```python
f = Flow().add(
    name='fast_executor').add(
    name='slow_executor', uses=MyTokenizer).add(
    name='pqlite_executor', uses='jinahub://PQLiteIndexer', uses_with={
      'dim': 5215,
      'metric': 'cosine'
    },
    uses_metas={'workspace': 'CHANGE-TO-YOUR-PATH/workspace'},
    install_requirements=True,
    shards=2,
)
```

Now open your workspace directory, you'll find we created 2 shards to store your indexed `Documents`:
`YOUR-WORKSPACE-DIR/PQLiteIndexer/0/` and `YOUR-WORKSPACE-DIR/PQLiteIndexer/1/`.

### Different POLLING Strategies

When you have multiple shards, the default `polling` strategy is `any`.
Jina supports two `polling` strategies:

1. `any`: requests will be randomly assigned to one shard.
2. `all`: requests will be handled by all shards.

In practice, when you are indexing your `Documents`,
it's better to set `polling='any'` to only store the `Documents` into one shard to avoid duplicates.
On the other hand, at search time, the search requests should be across all shards.
Thus we should set `polling='all''`.

As a result, we need to config our `Flow` definition with a different `Polling` strategy:
The new `Flow`:

```python
# Config your polling strategy based on endpoints
# At index time, use ALL, at search time use ANY, the rest use ALL.
polling_config = {'/index': 'ANY', '/search': 'ALL', '*': 'ALL'}

f = Flow().add(
    name='fast_executor').add(
    name='slow_executor', uses=MyTokenizer).add(
    name='pqlite_executor', uses='jinahub://PQLiteIndexer', uses_with={
      'dim': 5215,
      'metric': 'cosine'
    },
    uses_metas={'workspace': 'CHANGE-TO-YOUR-PATH/workspace'},
    install_requirements=True,
    shards=2,
    polling=polling_config,
)
```

## Conclusion

Jina can help you scale out your applications easily.
Depending on your needs, if you want to increase the `Executor` throughput, use the `replicas` argument.
If you want to partition your data across multiple places,
use the `shards` with the `polling` strategy you want.