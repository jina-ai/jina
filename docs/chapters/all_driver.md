# List of 35 Drivers in Jina

This version of Jina includes 35 Drivers.

## Inheritances in a Tree View
- `BaseDriver`
   - `BaseExecutableDriver`
      - `BaseCraftDriver`
         - `ChunkCraftDriver`
         - `DocCraftDriver`
         - `SegmentDriver`
      - `BaseIndexDriver`
         - `KVIndexDriver`
            - `ChunkKVIndexDriver`
            - `DocKVIndexDriver`
         - `VectorIndexDriver`
      - `BaseScoreDriver`
         - `Chunk2DocScoreDriver`
      - `BaseSearchDriver`
         - `KVSearchDriver`
            - `ChunkKVSearchDriver`
            - `DocKVSearchDriver`
         - `VectorSearchDriver`
      - `BaseEncodeDriver`
         - `EncodeDriver`
   - `ControlReqDriver`
      - `RouteDriver`
   - `ForwardDriver`
   - `LogInfoDriver`
   - `WaitDriver`
   - `MergeDriver`
      - `MergeTopKDriver`
         - `ChunkMergeTopKDriver`
         - `DocMergeTopKDriver`
   - `TopKFilterDriver`
   - `TopKSortDriver`
   - `PruneDriver`
      - `ChunkPruneDriver`
      - `DocPruneDriver`
      - `ReqPruneDriver`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `BaseCraftDriver` | `jina.drivers.encode` |
| `BaseDriver` |   |
| `BaseEncodeDriver` | `jina.drivers.encode` |
| `BaseExecutableDriver` | `jina.drivers.prune` |
| `BaseIndexDriver` | `jina.drivers.encode` |
| `BaseScoreDriver` | `jina.drivers.encode` |
| `BaseSearchDriver` | `jina.drivers.encode` |
| `Chunk2DocScoreDriver` | `jina.drivers.score` |
| `ChunkCraftDriver` | `jina.drivers.craft` |
| `ChunkKVIndexDriver` | `jina.drivers.index` |
| `ChunkKVSearchDriver` | `jina.drivers.search` |
| `ChunkMergeTopKDriver` | `jina.drivers.reduce` |
| `ChunkPruneDriver` | `jina.drivers.prune` |
| `ControlReqDriver` | `jina.drivers.prune` |
| `DocCraftDriver` | `jina.drivers.craft` |
| `DocKVIndexDriver` | `jina.drivers.index` |
| `DocKVSearchDriver` | `jina.drivers.search` |
| `DocMergeTopKDriver` | `jina.drivers.reduce` |
| `DocPruneDriver` | `jina.drivers.prune` |
| `EncodeDriver` | `jina.drivers.encode` |
| `ForwardDriver` | `jina.drivers.prune` |
| `KVIndexDriver` | `jina.drivers.index` |
| `KVSearchDriver` | `jina.drivers.search` |
| `LogInfoDriver` | `jina.drivers.prune` |
| `MergeDriver` | `jina.drivers.prune` |
| `MergeTopKDriver` | `jina.drivers.reduce` |
| `PruneDriver` | `jina.drivers.prune` |
| `ReqPruneDriver` | `jina.drivers.prune` |
| `RouteDriver` | `jina.drivers.control` |
| `SegmentDriver` | `jina.drivers.craft` |
| `TopKFilterDriver` | `jina.drivers.prune` |
| `TopKSortDriver` | `jina.drivers.prune` |
| `VectorIndexDriver` | `jina.drivers.index` |
| `VectorSearchDriver` | `jina.drivers.search` |
| `WaitDriver` | `jina.drivers.prune` |