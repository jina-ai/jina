# Indexers on Jina Hub

The [Jina Hub](hub.jina.ai) offers multiple Indexers for different use-cases.
There are four major questions that should be answered, when deciding for an Indexer and its configuration.
In a lot of production use-cases Indexers heavily use {ref}`shards <./scaling/shards>` and {ref}`replicas <./scaling/replicas>`

## Does my data fit into memory?

What is your estimated total number `N` of Documents, that you want to index?
What is the average size `x` of a Document?
Does `N * x` fit into memory?

## How many requests per second (RPS) does the system need to handle?

RPS is typically used for knowing how big to scale distributed systems.
Depending on your use-case you might have completely different RPS expectations.

## What latency do your users expect?

Latency is typically measured via the p95 or p99 [percentile](https://en.wikipedia.org/wiki/Percentile).

```{admonition}
:class: tip

A webshop might want a really low latency in order to increase user experience.
A high-quality Q&A chatbot might be OK with having answers only after one or even several seconds.
```

## Do you need instant failure recovery?

When running any service in the cloud, it might always happen that the underlying machine gets killed.
Usually, a new machine will spawn and take over.
Anyhow, this might take some minutes.
If you need instant failure recovery, you need to use replicas.
Jina provides this via the [FaissPostgresSearcher](https://hub.jina.ai/executor/nflcyqe2) in combination with {ref}`replicas <./scaling/replicas>` inside {ref}`kubernetes (k8s) <./kubernetes>`.

| Index Size | RPS | Latency p95 | Best Indexer | configuration |
| --- | --- | --- | --- | --- |
| fit into memory | < 20 | any | [SimpleIndexer](https://hub.jina.ai/executor/zb38xlt4) | use default |
| any | > 20 | any | [FaissPostgresSearcher](https://hub.jina.ai/executor/nflcyqe2) | use k8s & [replicas] |
| not fit into memory | any | any | [FaissPostgresSearcher](https://hub.jina.ai/executor/nflcyqe2) | use shards |
| not fit into memory | > 20 | any | [FaissPostgresSearcher](https://hub.jina.ai/executor/nflcyqe2) | use k8s & shards & replicas|
| any | any | small | [FaissPostgresSearcher](https://hub.jina.ai/executor/nflcyqe2) | use k8s & shards & replicas|
