# List of 35 Drivers in Jina

This version of Jina includes 35 Drivers.

## Inheritances in a Tree View
- `BaseDriver`
   - `MergeDriver`
      - `MergeTopKDriver`
         - `ChunkMergeTopKDriver`
         - `DocMergeTopKDriver`
   - `BaseExecutableDriver`
      - `BaseIndexDriver`
         - `KVIndexDriver`
            - `ChunkKVIndexDriver`
            - `DocKVIndexDriver`
         - `VectorIndexDriver`
      - `BaseScoreDriver`
         - `Chunk2DocScoreDriver`
      - `BaseCraftDriver`
         - `ChunkCraftDriver`
         - `DocCraftDriver`
         - `SegmentDriver`
      - `BaseEncodeDriver`
         - `EncodeDriver`
      - `BaseSearchDriver`
         - `KVSearchDriver`
            - `ChunkKVSearchDriver`
            - `DocKVSearchDriver`
         - `VectorSearchDriver`
   - `TopKFilterDriver`
   - `TopKSortDriver`
   - `PruneDriver`
      - `ChunkPruneDriver`
      - `DocPruneDriver`
      - `ReqPruneDriver`
   - `ControlReqDriver`
      - `RouteDriver`
   - `ForwardDriver`
   - `LogInfoDriver`
   - `WaitDriver`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `BaseCraftDriver` | `jina.drivers.search` |
| `BaseDriver` |   |
| `BaseEncodeDriver` | `jina.drivers.search` |
| `BaseExecutableDriver` | `jina.drivers.control` |
| `BaseIndexDriver` | `jina.drivers.search` |
| `BaseScoreDriver` | `jina.drivers.search` |
| `BaseSearchDriver` | `jina.drivers.search` |
| `Chunk2DocScoreDriver` | `jina.drivers.score` |
| `ChunkCraftDriver` | `jina.drivers.craft` |
| `ChunkKVIndexDriver` | `jina.drivers.index` |
| `ChunkKVSearchDriver` | `jina.drivers.search` |
| `ChunkMergeTopKDriver` | `jina.drivers.reduce` |
| `ChunkPruneDriver` | `jina.drivers.prune` |
| `ControlReqDriver` | `jina.drivers.control` |
| `DocCraftDriver` | `jina.drivers.craft` |
| `DocKVIndexDriver` | `jina.drivers.index` |
| `DocKVSearchDriver` | `jina.drivers.search` |
| `DocMergeTopKDriver` | `jina.drivers.reduce` |
| `DocPruneDriver` | `jina.drivers.prune` |
| `EncodeDriver` | `jina.drivers.encode` |
| `ForwardDriver` | `jina.drivers.control` |
| `KVIndexDriver` | `jina.drivers.index` |
| `KVSearchDriver` | `jina.drivers.search` |
| `LogInfoDriver` | `jina.drivers.control` |
| `MergeDriver` | `jina.drivers.control` |
| `MergeTopKDriver` | `jina.drivers.reduce` |
| `PruneDriver` | `jina.drivers.control` |
| `ReqPruneDriver` | `jina.drivers.prune` |
| `RouteDriver` | `jina.drivers.control` |
| `SegmentDriver` | `jina.drivers.craft` |
| `TopKFilterDriver` | `jina.drivers.control` |
| `TopKSortDriver` | `jina.drivers.control` |
| `VectorIndexDriver` | `jina.drivers.index` |
| `VectorSearchDriver` | `jina.drivers.search` |
| `WaitDriver` | `jina.drivers.control` |