# Indexers Benchmark

In this page we show the performance capabilities of the different Indexers available in Jina Hub.

## Results

In the below graphs you can see the performance, in terms of speed and evaluation.
Speed is reported for query time, in total seconds.
Evaluation is provided as recall, out of the `top_k` 100.
The tables are sorted by `time_search`.

```{include} bench/gist.md
```

```{include} bench/sift.md
```

```{include} bench/sift1bil.md
```

## Indexers

The purpose is to compare how they each scale, both with the amount of Documents indexed and with the embedding dimensionality.
We have restricted our selection to the following:

- [SimpleIndexer](https://hub.jina.ai/executor/zb38xlt4)
- [FaissSearcher](https://hub.jina.ai/executor/gilkzt3f)
- [HNSWSearcher](https://hub.jina.ai/executor/jdb3vkgo)
- [RiiSearcher](https://hub.jina.ai/executor/ksr1lmku)

`SimpleIndexer` is based on doing exhaustive search across all the Documents.
However, FAISS, HNSW and Rii are based on different approximate nearest neighbor approaches.
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


