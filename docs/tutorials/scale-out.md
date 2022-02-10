# Executor Scale-Out With Replicas & Shards

```{article-info}
:avatar: avatars/bo.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Bo @ Jina AI
:date: February 8, 2022
```

## Overview

A typical Jina `Flow` orchestrates multiple `Executors`.
By default, a Jina `Executor` runs with a single `Replica` and `Shard`.
Some `Executor` in the Flow might be less performant than other `Executors`,
this could be a performance bottleneck when you deploy your Jina service to production environment 

Luckily, Jina `Flow` allows you to config the number of `Replicas` and `Shards`.
`Replica` is used to increase `Executor` throughput and availability.
`Shard` is used for data partitioning.
In this tutorial, we'll dive into these two concepts and see how you can make use of `Replica` and `Shard` to scale out your `Executor`.

## Before you start
<!-- Delete this section if your readers can go to the steps without requiring any prerequisite knowledge. -->
Before you begin, make sure you meet these prerequisites:

* You have a good understanding of Jina [Flow](../fundamentals/flow/index.md).
* You have a good understanding of Jina [Executor](../fundamentals/executor/index.md)
* Please install several dependencies , includes jina and sklearn.

## Speed-Up A Slow Executor: Replicas

### Context

Imaging you are building a text search system and your have an `Executor` to transform text to it's [tf-idf](https://en.wikipedia.org/wiki/Tf-idf) vector representation.
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

And we create a `Flow` and make use some text corpus from sklearn to use this `Executor`:

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

### Scale-Up your Executor

When you start your `Flow`, you might discover to process all these text corpus, it takes a while:

```python
with f:
    results_da = f.post('/foo', news_generator, show_progress=True)
```

As Jina reported, it takes around 6 seconds to accomplish the task.
6 seconds sounds reasonable (at index time), but bear in mind that this is just a test corpus.
What if you needs to index millions of documents?

```shell
           Flow@2011375[I]:🎉 Flow is ready to use!                                        
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:52775
	🔒 Private network:	172.31.29.177:52775
	🌐 Public address:	54.93.57.58:52775
⠇       DONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━ 0:00:06 18.1 step/s . 115 steps done in 6 seconds
```

Jina allows you to scale your `Executor` very easily, with only one configuration:

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

Instead of scale an `Executor` at creation time,
we can scale an `Executor` after `Flow` being created, by calling `scale` method,
not only scale up, but also scale down.
For instance,
you want to scale up and scale down an `Executor`:

```python
f = Flow().add(name='fast_executor').add(name='slow_executor', uses=MyTokenizer, replicas=2)
f.scale('slow_executor', replicas=3)  # scale up from 2 to 3
f.scale('slow_executor', replicas=1)  # scale down from 3 to 1
```

Quite intuitive, right? In a later section,
we'll introduce what `replicas` means under different deployment options.

## Split Data over Machines: Shards

### Context

### Partitioning your Data

### Different POOLING Strategies

## Concept Alignment: How does it work on Localhost, Docker and K8s

## Conclusion

Jina can help you scale-out your applications easily.
Depending on your needs, if you want to increase `Executor` throughput, use `replicas` argument.
If you want to partition your data across multiple places,
use `shards` with `pooling` strategy you want.