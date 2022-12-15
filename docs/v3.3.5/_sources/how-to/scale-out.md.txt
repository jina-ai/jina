(scale-out)=
# How to Scale Out Your Executor

## Overview

A Jina `Flow` orchestrates multiple `Executors`.
By default, a Jina `Executor` runs with a single `replica` and `shard`.
Some `Executor` in the Flow might be less performant than others,
this could turn into a performance bottleneck in your Jina application.

To solve this, Jina `Flow` allows you to config the number of `replicas` and `shards`.
`replica` is used to increase `Executor` throughput and availability.
`shard` is used for data partitioning.

In this document, we'll dive into these two concepts and see how you can make use of `replicas` and `shards` to scale out your `Executor`.

## Before you start
<!-- Delete this section if your readers can go to the steps without requiring any prerequisite knowledge. -->
Before you begin, make sure you meet these prerequisites:

* You have a good understanding of Jina [Flow](../fundamentals/flow/index.md).
* You have a good understanding of Jina [Executor](../fundamentals/executor/index.md)
* Please install the following dependencies if you haven't:


```shell
pip install jina==3.0.0
pip install sklearn==1.0.2
pip install pqlite==0.2.3
```

## Speed up a slow Executor: Replicas

### Context

Imagine you are building a text-based search system and you have an `Executor` to transform text to its [tf-idf](https://en.wikipedia.org/wiki/Tf-idf) vector representation.
This could become a performance bottleneck to your search system.
The Executor looks like this:

```python
from jina import Executor, requests
from docarray import Document

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.datasets import fetch_20newsgroups

# we use a test corpus from scikit-learn
data, _ = fetch_20newsgroups(
    shuffle=True,
    random_state=1,
    return_X_y=True,
)

vectorizer = TfidfVectorizer()
vectorizer.fit(data)


def news_generator():
    for item in data:
        yield Document(text=item)


class MyVectorizer(Executor):
    @requests
    def vectorize(self, docs, **kwargs):
        # Extract all text from jina document and vectorize
        X = vectorizer.transform(docs.contents)
        # Assign tf-idf representation as document embeddings
        docs.embeddings = X
```

And we create a `Flow` and make use this `Executor`:

```python
from jina import Flow

f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyVectorizer)
```

### Scale up an Executor

When you start your `Flow`, you might discover to process all the text corpus, this process takes a while:

```python
with f:
    f.post('/foo', news_generator, show_progress=True)
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
+ f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyVectorizer, replicas=2)
- f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyVectorizer)
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
Quite intuitive, right?
If you are deploying Jina with K8s, you can consider this `Executor` as a K8s `Deployment` and each `replica` as a K8s `Pod`.

## Split data into partitions: Shards

### Context

Now with your text corpus encoded as TF-IDF embeddings,
it's time to save the results.
We'll use Jina's [PQLiteIndexer](https://hub.jina.ai/executor/pn1qofsj) to persist our embeddings for fast Approximate Nearest Neighbor Search.

And you add this `PQLiteIndexer` to your Flow:

```python
from jina import Flow

f = (
    Flow()
    .add(name='fast_executor')
    .add(name='slow_executor', uses=MyVectorizer)
    .add(
        name='pqlite_executor',
        uses='jinahub://PQLiteIndexer/v0.2.3-rc',
        uses_with={
            'dim': 130107,  # the dimension is fitted on the corpus in news dataset
            'metric': 'cosine',
        },
        workspace='CHANGE-TO-YOUR-PATH/workspace',
        install_requirements=True,
    )
)
```

### Partitioning the data

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
f = (
    Flow()
    .add(name='fast_executor')
    .add(name='slow_executor', uses=MyVectorizer)
    .add(
        name='pqlite_executor',
        uses='jinahub://PQLiteIndexer',
        uses_with={'dim': 130107, 'metric': 'cosine'},
        workspace='CHANGE-TO-YOUR-PATH/workspace',
        install_requirements=True,
        shards=2,
    )
)
```

Now open your workspace directory, you'll find we created 2 shards to store your indexed `Documents`:
`YOUR-WORKSPACE-DIR/PQLiteIndexer/0/` and `YOUR-WORKSPACE-DIR/PQLiteIndexer/1/`.

### Different polling strategies

When you have multiple shards, the default `polling` strategy is `any`.
Jina supports two `polling` strategies:

1. `any`: requests will be randomly assigned to one shard.
2. `all`: requests will be handled by all shards.

In practice, when you are indexing your `Documents`,
it's better to set `polling='any'` to only store the `Documents` into one shard to avoid duplicates.
On the other hand, at search time, the search requests should be across all shards.
Thus we should set `polling='all''`.

As a result, we need to config our `Flow` definition with a different `polling` strategy:
The new `Flow`:

```python
# Config your polling strategy based on endpoints
# At index time, use ALL, at search time use ANY, the rest use ALL.
polling_config = {'/index': 'ANY', '/search': 'ALL', '*': 'ALL'}

f = (
    Flow()
    .add(name='fast_executor')
    .add(name='slow_executor', uses=MyVectorizer)
    .add(
        name='pqlite_executor',
        uses='jinahub://PQLiteIndexer/v0.2.3-rc',
        uses_with={'dim': 130107, 'metric': 'cosine'},
        workspace='CHANGE-TO-YOUR-PATH/workspace',
        install_requirements=True,
        shards=2,
        polling=polling_config,
    )
)
```

It should be noted that Jina will automatically *reduce* your results given multiple shards.
For instance, when you are searching across multiple shards,
Jina will collect `matches` from all `shards` and return the reduced results.

## Conclusion

Jina can help you scale out your applications easily and effectively.
Depending on your needs, if you want to increase the `Executor` throughput, use the `replicas` argument.
If you want to partition your data across multiple places,
use the `shards` with the `polling` strategy you want.