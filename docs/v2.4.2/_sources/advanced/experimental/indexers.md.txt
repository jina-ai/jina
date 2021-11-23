# Indexers on Jina Hub

Indexers are a subtype of Hub Executors that store or retrieve data. They are designed to replace `DocumentArray` and `DocumentArrayMemmap` in large-scale applications.

They are split by usage and interface. These types are:

```{tab} Storage

This category is for *storing* data, in a CRUD-like interface. These Executors are reliable and performant in write/read/update/delete operations. They can only search by a Document's `id`.

Example Hub Executors:
 - [PostgreSQLStorage](https://hub.jina.ai/executor/d45rawx6)
 - [MongoDBStorage](https://hub.jina.ai/executor/3e1sp6fp)
 - [LMDBStorage](https://hub.jina.ai/executor/scdc6dop)
 - [RedisStorage](https://hub.jina.ai/executor/k0iqqtus)
```
```{tab} Vector Searcher
These usually implement a form of similarity search, based on the embeddings created by the encoders you have chosen in your Flow.

Example Hub Executors:
 - [FaissSearcher](https://hub.jina.ai/executor/gilkzt3f)
 - [AnnoySearcher](https://hub.jina.ai/executor/wiu040h9) 
```
```{tab} Compound Indexer
Compound indexer usually made up of a vector-based searcher, for computing the most similar matches, and a storage, for retrieving the match's original metadata.

Example Hub Executors:
 - [FaissLMDBSearcher](https://hub.jina.ai/executor/g57rla9l)
 - [FaissPostgresIndexer](https://hub.jina.ai/executor/ugatwtp8)
 
 If you want to develop one like these, check the guide {ref}`here <compound-executor>`.
```

```{tip}
Besides, there are two types of special indexer,

- [DocCache](https://hub.jina.ai/executor/3klmcx6r). It is not used for storing and retrieving data directly, but for caching and avoiding duplicating of data during the indexing process.
- [MatchMerger](https://hub.jina.ai/executor/mruax3k7). It is used for merging the results retrieved from sharding. It merges the results of shards by aggregating all matches by the corresponding Document in the original search request. 

```

## CRUD operations and the Executor endpoints

The Executors implemented and provided by Jina implement a CRUD interface as follows:

| Operation  | Endpoint  | Implemented in |
|------------|-----------|----------------|
| **C**reate | `/index`  | Storage        |
| **R**ead   | `/search` | Searcher       |
| **U**pdate | `/update` | Storage        |
| **D**elete | `/delete` | Storage        |

The Create, Update, Delete operations are implemented by the Storage Indexers, while the Read operation is implemented in the `/search` endpoints in the Search Indexers. 
The `/search` endpoints do not correspond perfectly with the Read operation, as it _searches_ for similar results, and does not return a specific Document by id.
Some Indexers do implement a `/fill_embedding` endpoint, which functions as a Read by id.
Please refer to the specific documentation or implementation of the Executor for details.

## Indexing vs Searching Operations

The recommended usage of these Executors is to split them into Indexing vs Search Flows.
In the Indexing Flow, you perform write, update, and delete. 
In order to search them, you need to start a Search Flow, dump the data from the Index Flow, and load it into the Query Flow.

See below figure for how this would look like:

```{figure} ../../../.github/images/replicas.png
:width: 80%
:align: center
```

In the above case, the Storage could be the [PostgreSQL](https://hub.jina.ai/executor/d45rawx6)-based Storage, while the Query Flow could be based on [FaissPostgresIndexer](https://hub.jina.ai/executor/ugatwtp8).

```{tip}
For a showcase code, check our [integration tests](https://github.com/jina-ai/executors/tree/main/tests/integration/psql_dump_reload).
```

The split between indexing and search Flows allows you to continuously serve requests in your application (in the search Flow), while still being able to write or modify the underlying data. Then when you want to update the state of the searchable data for your users, you perform a dump and rolling update.

(dump-rolling-restart)=
## Dump and Rolling Update

The communication between index and search Flows is done via this pair of actions.
The **dump** action tells the indexer to export its internal data (from whatever format it stores it in) to a disk location, optimized to be read by the shards in your search Flow.
At the other end, the **rolling update** tells the search Flow to recreate its internal state with the new version of the data.

Looking at the [test](https://github.com/jina-ai/executors/tree/main/tests/integration/psql_dump_reload/test_dump_psql.py), we can see how this is called:

```python
flow_storage.post(
     on='/dump',
     target_peapod='indexer_storage',
     parameters={
         'dump_path': dump_path,
         'shards': shards,
         'timeout': -1,
     },
 )
```

where

- `flow_storage` is the Flow with the storage Indexer
- `target_peapod` is the name of the Executor, defined in your `flow.yml`
- `dump_path` is the path (on local disk) where you want the data to be stored. **NOTE** The folder needs to be empty. Otherwise, the dump will be cancelled. 
- `shards` is the number of shards you have in your search Flow. **NOTE** This doesn't change the value in the Flow. You need to keep track of how you configured your search Flow

For performing the **rolling update**, we can see the usage in the same test:

```python
flow_query.rolling_update(pod_name='indexer_query', dump_path=dump_path)
```

where

- `flow_query` is the Flow with the searcher Indexer
- `pod_name` is the name of the Executor, defined in your `flow.yml`
- `dump_path` is the folder where you exported the data, from the above **dump** call

```{note}

`dump_path` needs to be accessible by local reference. It can however be a network location / internal Docker location that you have mapped 

```

## Indexer Cheat Sheet

| Index Size | RPS | Latency p95 | Best Indexer + configuration |
| --- | --- | --- | --- |
| fit into memory | < 20 | any | [SimpleIndexer](https://hub.jina.ai/executor/zb38xlt4) + use default |
| any | > 20 | any | [FaissPostgresIndexer](https://hub.jina.ai/executor/ugatwtp8) + use k8s & replicas |
| not fit into memory | any | any | [FaissPostgresIndexer](https://hub.jina.ai/executor/ugatwtp8) + use shards |
| not fit into memory | > 20 | any | [FaissPostgresIndexer](https://hub.jina.ai/executor/ugatwtp8) + use k8s & shards & replicas|
| any | any | small | [FaissPostgresIndexer](https://hub.jina.ai/executor/ugatwtp8) + use k8s & shards & replicas|


The [Jina Hub](http://hub.jina.ai) offers multiple Indexers for different use-cases.
In a lot of production use-cases Indexers heavily use {ref}`shards <shards>` and {ref}`replicas <replicas>`.
There are four major questions that should be answered, when deciding for an Indexer and its configuration.


### Does my data fit into memory?

Estimated the total number `N` of Documents that you want to index.
Understand the average size `x` of a Document.
Does `N * x` fit into memory?

### How many requests per second (RPS) does the system need to handle?

RPS is typically used for knowing how big to scale distributed systems.
Depending on your use-case you might have completely different RPS expectations.

### What latency do your users expect?

Latency is typically measured via the p95 or p99 [percentile](https://en.wikipedia.org/wiki/Percentile).
Meaning, how fast are 95% or 99% percent of the requests answered.

```{admonition} Tip
:class: tip

A webshop might want a really low latency in order to increase user experience.
A high-quality Q&A chatbot might be OK with having answers only after one or even several seconds.
```

### Do you need instant failure recovery?

When running any service in the cloud, an underlying machine could die at any time.
Usually, a new machine will spawn and take over.
Anyhow, this might take some minutes.
If you need instant failure recovery, you need to use replicas.
Jina provides this via the [FaissPostgresIndexer](https://hub.jina.ai/executor/ugatwtp8) in combination with {ref}`replicas <replicas>` inside {ref}`kubernetes (k8s) <kubernetes>`.


