(scale-out)=
# Scale out with replicas and shards

A Jina {class}`~jina.Flow` orchestrates multiple {class}`~jina.Executor`s.
By default, an Executor runs with a single `replica` and `shard`.
Some Executors in the Flow may be less performant than others,
which could cause performance bottlenecks in an application.

To solve this, you can configure the number of `replicas` and `shards`.

- `replica`s increase Executor throughput and availability.
- `shard`s partition data in different storage locations.

Before you start, ensure you understand [Flows](../fundamentals/flow/index.md) and [Executors](../fundamentals/executor/index.md)

## Speed up a slow Executor: Replicas

### Context

Imagine you're building a text-based search system and you have an {class}`~jina.Executor` to transform text to a [tf-idf](https://en.wikipedia.org/wiki/Tf-idf) vector representation. This could become a performance bottleneck in the search system.

The Executor looks like this:

```python
from jina import Executor, requests, Document

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

Let's create a Flow and use this Executor:

```python
from jina import Flow

f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyVectorizer)
```

### Scale up an Executor

When you start the {class}`~jina.Flow`, you may find it takes a while to process the whole text corpus:

```python
with f:
    f.post('/foo', news_generator, show_progress=True)
```

As Jina reports, it takes around six seconds to complete the task.
This sounds reasonable (at index time), but bear in mind that this is just a test corpus.
What if you need to index millions of Documents?

```shell
           Flow@2011375[I]:🎉 Flow is ready to use!                                        
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:52775
	🔒 Private network:	172.31.29.177:52775
	🌐 Public address:	54.93.57.58:52775
⠇       DONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━ 0:00:06 18.1 step/s . 115 steps done in 6 seconds
```

To do this, you can scale a {class}`~jina.Executor` with just one parameter change:

```diff
+ f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyVectorizer, replicas=2)
- f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyVectorizer)
```

Let's see how it performs given two `replicas`:

```shell
           Flow@2011375[I]:🎉 Flow is ready to use!                                        
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:57040
	🔒 Private network:	172.31.29.177:57040
	🌐 Public address:	54.93.57.58:57040
⠇       DONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━ 0:00:03 37.0 step/s . 115 steps done in 3 seconds
```

As you can see, it now only takes three seconds to finish the task. If you deploy Jina with Kubernetes, you can consider this `Executor` as a Kubernetes `Deployment` and each `replica` as a `Pod`.

## Split data into partitions: Shards

### Context

Now with the text corpus encoded as TF-IDF embeddings, it's time to save the results.
We'll use Jina's [ANNLiteIndexer](https://cloud.jina.ai/executor/7yypg8qk) to persist the embeddings for fast Approximate Nearest Neighbor Search.

Let's add `ANNLiteIndexer` to the Flow:

```python
from jina import Flow

f = (
    Flow()
    .add(name='fast_executor')
    .add(name='slow_executor', uses=MyVectorizer)
    .add(
        name='pqlite_executor',
        uses='jinahub://ANNLiteIndexer/v0.2.3-rc',
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

Let's run the {class}`~jina.Flow`to index the data:
```python
with f:
    f.post(on='/index', inputs=news_generator, show_progress=True)
```

`ANNLiteIndexer` saves the indexed Documents to the specified `workspace` (directory).
Since the default number of shards is one, all data is saved to `YOUR-WORKSPACE-DIR/ANNLiteIndexer/0/` where `0` is the shard id.

To distribute data to different places, use `shards` to specify the number of shards.

```python
f = (
    Flow()
    .add(name='fast_executor')
    .add(name='slow_executor', uses=MyVectorizer)
    .add(
        name='pqlite_executor',
        uses='jinahub://ANNLiteIndexer',
        uses_with={'dim': 130107, 'metric': 'cosine'},
        workspace='CHANGE-TO-YOUR-PATH/workspace',
        install_requirements=True,
        shards=2,
    )
)
```

Now open the workspace directory. You'll see we created two shards to store the indexed Documents:
`YOUR-WORKSPACE-DIR/ANNLiteIndexer/0/` and `YOUR-WORKSPACE-DIR/ANNLiteIndexer/1/`.

### Polling strategies

Jina supports two `polling` strategies:

1. `any`: requests are randomly assigned to one shard. (Default for multiple shards)
2. `all`: requests are handled by all shards.

In practice, when you are indexing Documents,
it's better to set `polling='any'` to store them in only one shard to avoid duplicates.
On the other hand, at search time, search requests should be made across all shards,
so we should set `polling='all'`.

As a result, we need to configure the `Flow` with a different `polling` strategy:

The new `Flow`:

```python
# Config polling strategy based on endpoints
# At index time, use ALL, at search time use ANY, the rest use ALL.
polling_config = {'/index': 'ANY', '/search': 'ALL', '*': 'ALL'}

f = (
    Flow()
    .add(name='fast_executor')
    .add(name='slow_executor', uses=MyVectorizer)
    .add(
        name='pqlite_executor',
        uses='jinahub://ANNLiteIndexer/v0.2.3-rc',
        uses_with={'dim': 130107, 'metric': 'cosine'},
        workspace='CHANGE-TO-YOUR-PATH/workspace',
        install_requirements=True,
        shards=2,
        polling=polling_config,
    )
)
```

Note that Jina automatically *reduces* the results given multiple shards.
For instance, when you are searching across multiple shards,
Jina collects `matches` from all `shards` and returns the reduced results.

## Conclusion

Jina can help you scale out applications easily and effectively.
Depending on your needs, you can increase `Executor` throughput using the `replicas` argument.
If you want to partition data across multiple places, use the `shards` with the `polling` strategy you want.
