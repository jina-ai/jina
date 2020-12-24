# Common Design Patterns

Jina is a really flexible AI-powered neural search framework and is designed to enable any pattern that can be framed as a neural search problem. However, there are basic common patterns that show up when developing search solutions with Jina:

## CompoundIndexer (Vector + KV Indexers)

For neural search applications, it helps to use a `CompoundIndexer` in the same Pod for both the index and query Flows. The following YAML file shows an example of this pattern:

```yaml
!CompoundIndexer
components:
  - !NumpyIndexer
    with:
      index_filename: vectors.gz
      metric: cosine
    metas:
      name: vecIndexer
  - !BinaryPbIndexer
    with:
      index_filename: values.gz
    metas:
      name: kvIndexer  # a customized name
metas:
  name: complete indexer
```

The above YAML creates a Flow that:

* Acts as a single indexer
* Lets you seamlessly query the index with the embedding vector from any upstream encoder
* Returns the binary information in the key-value index in the Pod's response message.
 
The `VectorIndexer`:

* Retrieves the most relevant Documents by finding similarities in the embedding space
* Uses the key-value index to extract meaningful data and fields from those Documents

## Text Document Segmentation

A common search pattern is storing long text documents in an index to retrieve them later using short sentences. A single embedding vector per long text document is not the proper way to do this: It makes it hard to extract a single semantically-meaningful vector from a long document. Jina solves this by introducing [Chunks](https://github.com/jina-ai/jina/tree/master/docs/chapters/101#document--chunk). The common scenario is to have a `crafter` segmenting the document into smaller parts (typically short sentences) followed by an NLP-based encoder. 

```yaml
!Sentencizer
with:
  min_sent_len: 2
  max_sent_len: 64
```
```yaml
!TransformerTorchEncoder
with:
  pooling_strategy: auto
  pretrained_model_name_or_path: distilbert-base-cased
  max_length: 96
```

This way a single document contains `N` different Chunks that are later independently encoded by a downstream encoder. This lets Jina query the index using a short sentence as input, where similarity search can be applied to find the most common Chunks. This way the same Document can be retrieved based on searching different parts of it.

For instance, a text document containing 3 sentences can be decomposed into 3 Chunks:

`Someone is waiting at the bus stop. John looks surprised, his face seems familiar` ->
[`Someone is waiting at the bus stop`, `John looks surprised`, `his face seems familiar`]

This lets us retrieve the Document from different `input` sentences that match any of these 3 parts. For instance, these 3 different inputs could lead to the extraction of the same document by targeting 3 different Chunks:

- A standing guy -> Someone is waiting at the bus stop.
- He is amazed` -> John looks surprised.
- a similar look -> his face seems familiar.

## Indexers at Different Depth Levels

In a configuration like the one for *Text Document Segmentation*, we need different levels of indexing. The system needs to keep the data related to the Chunks as well as the information of the original documents. This way: 

1. The actual search is performed at the Chunk level following the `CompoundIndexer` pattern.
2. Then the Document indexer works as a final step to extract the actual Documents expected by the user.
 
To implement this, two common structures appear in `index` and `query`. In an `index` flow, these two indexers work in parallel:

* The `chunk indexer` gets messages from an `encoder`
* The `doc indexer` can get the documents even from the `gateway`.

```yaml
!Flow
pods:
  encoder:
    uses: BaseEncoder
  chunk_indexer:
    uses: CompoundIndexer
  doc_indexer:
    uses: BinaryPbIndexer
    needs: gateway
  join_all:
    uses: _pass
    needs: [doc_indexer, chunk_indexer]
```

However, at query time the Document and Chunk indexers work sequentially. Normally the Document would get messages from the Chunk indexer with a `Chunk2DocRanker` Pod in the middle of the Flow. The `ranker` would rank the Chunks by relevance and reduce the results to the parent IDs, enabling the `doc indexer` to extract the original Document's binary information.

```yaml
!Flow
  encoder:
    uses: BaseEncoder
  chunk_indexer:
    uses: CompoundIndexer
  ranker:
    uses: Chunk2DocRanker
  doc_indexer:
    uses: BinaryPbIndexer
```

## Switch Vector Indexer at Query Time

Jina lets you decide which kind of vector index to use when exposing the system to be queried. Almost all of Jina's advanced vector indexers inherit from `BaseNumpyIndexer`. These classes only override methods related to querying the index, but not the ones related to storing vectors, meaning they all store vectors in the same format. Jina takes advantage of this, and has the flexibility to offer the same vector data in different vector indexer types. To implement this functionality there are two things to consider, one for indexing and one for querying.

### Indexing

At index time, we use `NumpyIndexer`. It is important that the `Pod` containing this Executor ensures `read_only: False`. This way, the same indexer can be reconstructed from binary form, which contains information of the vectors (dimensions, ...) that are needed to have it work at query time.

```yaml
!NumpyIndexer
with:
  index_filename: 'vec.gz'
metas:
  name: wrapidx
```

### Querying

At query time, we use `NumpyIndexer` as `ref_indexer` for any advanced indexer inheriting from `BaseNumpyIndexer` (see `AnnoyIndexer`, `FaissIndexer`, ...).

```yaml
!FaissIndexer
with:
  ref_indexer:
    !NumpyIndexer
    metas:
      name: wrapidx
    with:
      index_filename: 'vec.gz'
```

In this case, this construction lets the `FaissIndexer` use the `vectors` stored by the indexer named `wrapidx`. 


## Override parameters using QuerySet

We can override parameter values in flows with the help of `QuerySet`. `querySet` is a set of `QueryLang` protobuf messages that can be sent along with any `Request`. It is useful to dynamically override parameters of a driver for a specific request. (Not every parameter is able to be overriden)   

This `QueryLang` has 3 main fields:
- name: A name of the driver that will be overriden (the exact class name). For now any driver in the Flow of this class will be affected by this `QueryLang`
- parameters: A key-value map where the key is the parameter to be overriden and the value the value that it will be used in the request
- priority: The priority this `QueryLang` has with respect to potential defaults of the driver.

For a driver to be able to override its parameters and read from the `QueryLang` messages it needs to do 2 things:
- Implement `QuerySetReader` as a `mix-in` class
- Declare the attribute with an underscore prefix, i.e (`self._top_k` to have `top_k` as an attribute with the potential to be overriden)
 
Suppose we want to override `VectorSearchDriver's` top_k value of 10 with 20 in the below pod. We can see that `VectorSearchDriver` fullfills the requirements:

```python
class VectorSearchDriver(QuerySetReader, BaseSearchDriver):
    def __init__(self, top_k: int = 50, fill_embedding: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ...
        self._top_k = top_k
        ...
```

The pod is defined as taking 10 for its `top_k` parameter in the `VectorSearchDriver`.
 
```yaml
!CompoundIndexer
components:
  - !NumpyIndexer
    with:
      index_filename: vec.gz
      metric: cosine
    metas:
      name: vecidx
      workspace: $JINA_DIR
  - !BinaryPbIndexer
    with:
      index_filename: doc.gz
    metas:
      name: docidx
      workspace: $JINA_DIR
metas:
  name: chunk_indexer
  workspace: $JINA_DIR
requests:
  on:
    IndexRequest:
      - !VectorIndexDriver
        with:
          executor: vecidx
          traversal_paths: ['r']
      - !KVIndexDriver
        with:
          executor: docidx
          traversal_paths: ['r']
    [SearchRequest]:
      - !VectorSearchDriver
        with:
          executor: vecidx
          top_k: 10
          traversal_paths: ['r']
      - !KVSearchDriver
        with:
          executor: docidx
          traversal_paths: ['m']
```

We construct a queryset `top_k_queryset` which defines to use a top_k value of 20 for `VectorSearchDriver`.

```python
    top_k_queryset = jina_pb2.QueryLang()
    top_k_queryset.name = 'VectorSearchDriver'
    top_k_queryset.priority = 1
    top_k_queryset.parameters['top_k'] = 20
```

Passing `top_k_queryset` to `flow.search` will override `top_k` value of `10` with `20` in the `VectorSearchDriver`.
Note that more than one `queryset` can be passed with any request.

```python
    with Flow.load_config('flow.yml') as search_flow:
        search_flow.search(input_fn=docs, output_fn=print_results, queryset=[top_k_queryset])
```

## The Score Field

In ranking document matches, Jina uses several algorithms to compute the *relevance* of a document given a specific query. This is stored as a numeric value in the `score` field of a `match`, both at a `document` level and at the `chunk` level. This field can mean either "smaller is better" (*distance*) or "larger is better" (*similarity*, *relevance*).  

As, an example, the `NumpyIndexer` uses k-NN (with various distance metrics) to calculate a *distance*, thus "smaller is better". On the other hand, the `MinRanker` uses the function *1/(1+s)* (where *s* is the min. score from all `chunks`) in order to "bubble up" the score from child `chunks` to the parent, thus "larger is better". There can be other metrics too.

This can pe problematic when deciding how to sort the results from a query. Fortunately, Jina provides the name of the operator that has performed the scoring:

```
/**
 * Represents the relevance model to `ref_id`
 */
message NamedScore {
    float value = 1; // value
    string op_name = 2; // the name of the operator/score function
    ...
}
```

Notice the field `op_name` in the above. As the comment suggests, this is the name of the operator that has performed the sorting (e.g. `NumpyIndexer`, or `MinRanker`). Based on this, the `value` field is either of type "smaller is better" or of type "larger is better". 

**Conclusion**: When sorting results, make sure you check the `document.score.op_name` in order to understand the direction of the score.

