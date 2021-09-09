# Indexers

Indexers are a subtype of Executors that store or retrieve data.
They are split by usage and interface. The types are:

1. [storage](https://github.com/jina-ai/executors/tree/main/jinahub/indexers/storage). This category is for *storing* data, in a CRUD-like interface. These Executors are reliable and performant in write/read/update/delete operations. They can only search by a Document's `id`.
2. [vector searchers](https://github.com/jina-ai/executors/tree/main/jinahub/indexers/searcher/) These usually implement a form of similarity search, based on the embeddings created by the encoders you have chosen in your Flow.
3. [compound](https://github.com/jina-ai/executors/tree/main/jinahub/indexers/searcher/compound) These are compound classes, usually made up of a vector-based searcher, for computing the most similar matches, and a storage, for retrieving the match's original metadata.
4. [DocCache](https://github.com/jina-ai/executors/tree/main/jinahub/indexers/DocCache). This is a special type of Indexer. It is not used for storing and retrieving data directly, but for caching and avoiding duplicating of data during the indexing process.
5. [MatchMerger](https://github.com/jina-ai/executors/tree/main/jinahub/indexers/merger/MatchMerger). This is another special type of Indexer. It is used for merging the results retrieved from sharding. It merges the results of shards by aggregating all matches by the corresponding Document in the original search request. 

## Indexing vs Searching Operations

The recommended usage of these Executors is to split them into Indexing vs Search Flows.
In the Indexing Flow, you perform write, update, and delete. 
In order to search them, you need to start a Search Flow, dump the data from the Index Flow, and load it into the Query Flow.

See below figure for how this would look like:

![](.github/images/replicas.png)

In the above case, the Storage could be the [PostgreSQL](https://github.com/jina-ai/executors/tree/main/jinahub/indexers/storage/PostgreSQLStorage)-based Storage, while the Query Flow could be based on [FaissPostgresSearcher](https://github.com/jina-ai/executors/tree/main/jinahub/indexers/searcher/compound/FaissPostgresSearcher).

For a showcase code, check our [integration tests](https://github.com/jina-ai/executors/tree/main/tests/integration/psql_dump_reload).

The split between indexing and search Flows allows you to continuously serve requests in your application (in the search Flow), while still being able to write or modify the underlying data. Then when you want to update the state of the searchable data for your users, you perform a dump and rolling update.

### Dump and Rolling Update

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

### Notes

- `dump_path` needs to be accessible by local reference. It can however be a network location / internal Docker location that you have mapped 
