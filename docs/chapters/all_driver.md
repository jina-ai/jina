# List of 35 Drivers in Jina

This version of Jina includes 35 Drivers.

## Inheritances in a Tree View
- `BaseDriver`
   - `TopKFilterDriver`
   - `TopKSortDriver`
   - `BaseExecutableDriver`
      - `BaseScoreDriver`
         - `Chunk2DocScoreDriver`
      - `BaseSearchDriver`
         - `KVSearchDriver`
            - `ChunkKVSearchDriver`
            - `DocKVSearchDriver`
         - `VectorSearchDriver`
      - `BaseEncodeDriver`
         - `EncodeDriver`
      - `BaseIndexDriver`
         - `KVIndexDriver`
            - `ChunkKVIndexDriver`
            - `DocKVIndexDriver`
         - `VectorIndexDriver`
      - `BaseCraftDriver`
         - `ChunkCraftDriver`
         - `DocCraftDriver`
         - `SegmentDriver`
   - `ControlReqDriver`
      - `RouteDriver`
   - `ForwardDriver`
   - `LogInfoDriver`
   - `WaitDriver`
   - `PruneDriver`
      - `ChunkPruneDriver`
      - `DocPruneDriver`
      - `ReqPruneDriver`
   - `MergeDriver`
      - `MergeTopKDriver`
         - `ChunkMergeTopKDriver`
         - `DocMergeTopKDriver`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `BaseCraftDriver` | `jina.drivers.craft` |
| `BaseDriver` |   |
| `BaseEncodeDriver` | `jina.drivers.craft` |
| `BaseExecutableDriver` | `jina.drivers.reduce` |
| `BaseIndexDriver` | `jina.drivers.craft` |
| `BaseScoreDriver` | `jina.drivers.craft` |
| `BaseSearchDriver` | `jina.drivers.craft` |
| `Chunk2DocScoreDriver` | `jina.drivers.score` |
| `ChunkCraftDriver` | `jina.drivers.craft` |
| `ChunkKVIndexDriver` | `jina.drivers.index` |
| `ChunkKVSearchDriver` | `jina.drivers.search` |
| `ChunkMergeTopKDriver` | `jina.drivers.reduce` |
| `ChunkPruneDriver` | `jina.drivers.prune` |
| `ControlReqDriver` | `jina.drivers.reduce` |
| `DocCraftDriver` | `jina.drivers.craft` |
| `DocKVIndexDriver` | `jina.drivers.index` |
| `DocKVSearchDriver` | `jina.drivers.search` |
| `DocMergeTopKDriver` | `jina.drivers.reduce` |
| `DocPruneDriver` | `jina.drivers.prune` |
| `EncodeDriver` | `jina.drivers.encode` |
| `ForwardDriver` | `jina.drivers.reduce` |
| `KVIndexDriver` | `jina.drivers.index` |
| `KVSearchDriver` | `jina.drivers.search` |
| `LogInfoDriver` | `jina.drivers.reduce` |
| `MergeDriver` | `jina.drivers.reduce` |
| `MergeTopKDriver` | `jina.drivers.reduce` |
| `PruneDriver` | `jina.drivers.reduce` |
| `ReqPruneDriver` | `jina.drivers.prune` |
| `RouteDriver` | `jina.drivers.control` |
| `SegmentDriver` | `jina.drivers.craft` |
| `TopKFilterDriver` | `jina.drivers.reduce` |
| `TopKSortDriver` | `jina.drivers.reduce` |
| `VectorIndexDriver` | `jina.drivers.index` |
| `VectorSearchDriver` | `jina.drivers.search` |
| `WaitDriver` | `jina.drivers.reduce` |