# List of 35 Drivers in Jina

This version of Jina includes 35 Drivers.

## Inheritances in a Tree View
- `BaseDriver`
   - `PruneDriver`
      - `ChunkPruneDriver`
      - `DocPruneDriver`
      - `ReqPruneDriver`
   - `MergeDriver`
      - `MergeTopKDriver`
         - `ChunkMergeTopKDriver`
         - `DocMergeTopKDriver`
   - `BaseExecutableDriver`
      - `BaseCraftDriver`
         - `ChunkCraftDriver`
         - `DocCraftDriver`
         - `SegmentDriver`
      - `BaseEncodeDriver`
         - `EncodeDriver`
      - `BaseScoreDriver`
         - `Chunk2DocScoreDriver`
      - `BaseSearchDriver`
         - `KVSearchDriver`
            - `ChunkKVSearchDriver`
            - `DocKVSearchDriver`
         - `VectorSearchDriver`
      - `BaseIndexDriver`
         - `KVIndexDriver`
            - `ChunkKVIndexDriver`
            - `DocKVIndexDriver`
         - `VectorIndexDriver`
   - `TopKFilterDriver`
   - `TopKSortDriver`
   - `ControlReqDriver`
      - `RouteDriver`
   - `ForwardDriver`
   - `LogInfoDriver`
   - `WaitDriver`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `BaseCraftDriver` | `jina.drivers.index` |
| `BaseDriver` |   |
| `BaseEncodeDriver` | `jina.drivers.index` |
| `BaseExecutableDriver` | `jina.drivers.control` |
| `BaseIndexDriver` | `jina.drivers.index` |
| `BaseScoreDriver` | `jina.drivers.index` |
| `BaseSearchDriver` | `jina.drivers.index` |
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