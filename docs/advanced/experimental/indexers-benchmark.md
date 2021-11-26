# Indexers Benchmark

In this page we will show the performance capabilities of the different indexers available in Jina Hub.
The purpose is to compare how they each scale, both with the amount of Documents indexed and with the embedding dimensionality.
We have restricted our selection to the following

- [SimpleIndexer](https://hub.jina.ai/executor/zb38xlt4)
- [FaissSearcher](https://hub.jina.ai/executor/gilkzt3f)
- [HNSWSearcher](https://hub.jina.ai/executor/jdb3vkgo)

`SimpleIndexer` is based on doing exhaustive search across all the Documents.
However, Both FAISS and HNSW are based on the approximate nearest neighbor approach. 
For each of these, we provide several configurations of parameters, in order to ascertain which behaves best.

## Datasets

We use three different datasets, each with different number of samples or dimensionality of vectors.
They are all based at the [IRISA](http://corpus-texmex.irisa.fr/) website.
The datasets are:

| **dataset** | **index vectors** | **dimensionality** | **query vectors** | **top_k** |
|:-----------:|:-----------------:|:------------------:|:-----------------:|:---------:|
| sift        | 1 million         | 128                | 10k               | 100       |
| gist        | 1 million         | 960                | 1k                | 100       |
| sift1b      | 1 billion         | 128                | 10k               | 1000      |

Note that out of the 1 billion dataset, we have only run a sub-sample of 10 and 20 million.
We have also only used a `top_k` value of 100.
The datasets provide ground-truths for the query vectors.

## Methodology

For each combination of configuration and dataset, we index a gradual subsampling of the dataset into the specific Indexer.
Indexing batch size is set to `1000`.
The FAISS Indexer requires training. 
This is done with a further sub-sampling of the index set.
This depended on the configuration parameters for the FAISS model.
Then we search with the respective search set, using a batch size of `1`, to mimic single query operations. 


## Results

[comment]: <> (TODO To store html plots somewhere and reference them here with iframes?)

In the below graphs you can see the performance, in terms of speed and evaluation.
Speed is reported for both index and query time, in total seconds.
Evaluation is provided in both precision and recall, out of the `top_k` 100.

<iframe src="https://www.w3schools.com"></iframe>

Here is the data in table form as well:

[comment]: <> (TODO)
