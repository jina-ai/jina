# List of 60 Drivers in Jina

This version of Jina includes 60 Drivers.

## Inheritances in a Tree View
- `BaseDriver`
   - `BaseRecursiveDriver`
      - `BaseExecutableDriver`
         - `BaseRankDriver`
            - `Chunk2DocRankDriver`
            - `CollectMatches2DocRankDriver`
            - `Matches2DocRankDriver`
         - `BaseIndexDriver`
            - `KVIndexDriver`
            - `VectorIndexDriver`
            - `BaseCacheDriver`
               - `TaggingCacheDriver`
         - `BaseEncodeDriver`
            - `MultiModalDriver`
            - `EncodeDriver`
         - `BaseSearchDriver`
            - `KVSearchDriver`
               - `LoadGroundTruthDriver`
            - `QuerySetReader`
               - `VectorFillDriver`
               - `VectorSearchDriver`
         - `BaseEvaluateDriver`
            - `FieldEvaluateDriver`
               - `NDArrayEvaluateDriver`
               - `RankEvaluateDriver`
               - `TextEvaluateDriver`
         - `CraftDriver`
            - `SegmentDriver`
         - `BasePredictDriver`
            - `BaseLabelPredictDriver`
               - `BinaryPredictDriver`
               - `OneHotPredictDriver`
                  - `MultiLabelPredictDriver`
            - `Prediction2DocBlobDriver`
      - `ReduceAllDriver`
         - `CollectEvaluationDriver`
         - `ConcatEmbedDriver`
      - `QuerySetReader`
         - `ExcludeQL`
            - `ExcludeReqQL`
               - `SelectReqQL`
            - `SelectQL`
         - `FilterQL`
         - `SortQL`
         - `ReverseQL`
         - `SliceQL`
      - `ConvertDriver`
         - `Blob2PngURI`
         - `Buffer2URI`
         - `Text2URI`
         - `URI2Buffer`
         - `URI2DataURI`
         - `URI2Text`
   - `BaseControlDriver`
      - `ControlReqDriver`
         - `RouteDriver`
            - `ForwardDriver`
            - `ReduceDriver`
      - `LogInfoDriver`
      - `WaitDriver`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `BaseCacheDriver` | `jina.drivers.cache` |
| `BaseControlDriver` | `jina.drivers.control` |
| `BaseDriver` |   |
| `BaseEncodeDriver` | `jina.drivers.predict` |
| `BaseEvaluateDriver` | `jina.drivers.predict` |
| `BaseExecutableDriver` | `jina.drivers.querylang.slice` |
| `BaseIndexDriver` | `jina.drivers.predict` |
| `BaseLabelPredictDriver` | `jina.drivers.predict` |
| `BasePredictDriver` | `jina.drivers.predict` |
| `BaseRankDriver` | `jina.drivers.predict` |
| `BaseRecursiveDriver` | `jina.drivers.control` |
| `BaseSearchDriver` | `jina.drivers.predict` |
| `BinaryPredictDriver` | `jina.drivers.predict` |
| `Blob2PngURI` | `jina.drivers.convert` |
| `Buffer2URI` | `jina.drivers.convert` |
| `Chunk2DocRankDriver` | `jina.drivers.rank` |
| `CollectEvaluationDriver` | `jina.drivers.reduce` |
| `CollectMatches2DocRankDriver` | `jina.drivers.rank` |
| `ConcatEmbedDriver` | `jina.drivers.reduce` |
| `ControlReqDriver` | `jina.drivers.control` |
| `ConvertDriver` | `jina.drivers.querylang.slice` |
| `CraftDriver` | `jina.drivers.predict` |
| `EncodeDriver` | `jina.drivers.encode` |
| `ExcludeQL` |   |
| `ExcludeReqQL` | `jina.drivers.querylang.select` |
| `FieldEvaluateDriver` | `jina.drivers.evaluate` |
| `FilterQL` |   |
| `ForwardDriver` | `jina.drivers.control` |
| `KVIndexDriver` | `jina.drivers.cache` |
| `KVSearchDriver` | `jina.drivers.search` |
| `LoadGroundTruthDriver` | `jina.drivers.evaluate` |
| `LogInfoDriver` | `jina.drivers.control` |
| `Matches2DocRankDriver` | `jina.drivers.rank` |
| `MultiLabelPredictDriver` | `jina.drivers.predict` |
| `MultiModalDriver` | `jina.drivers.encode` |
| `NDArrayEvaluateDriver` | `jina.drivers.evaluate` |
| `OneHotPredictDriver` | `jina.drivers.predict` |
| `Prediction2DocBlobDriver` | `jina.drivers.predict` |
| `QuerySetReader` | `jina.drivers.querylang.slice` |
| `QuerySetReader` | `jina.drivers.search` |
| `RankEvaluateDriver` | `jina.drivers.evaluate` |
| `ReduceAllDriver` | `jina.drivers.querylang.slice` |
| `ReduceDriver` | `jina.drivers.control` |
| `ReverseQL` |   |
| `RouteDriver` | `jina.drivers.control` |
| `SegmentDriver` | `jina.drivers.craft` |
| `SelectQL` | `jina.drivers.querylang.select` |
| `SelectReqQL` | `jina.drivers.querylang.select` |
| `SliceQL` |   |
| `SortQL` |   |
| `TaggingCacheDriver` | `jina.drivers.cache` |
| `Text2URI` | `jina.drivers.convert` |
| `TextEvaluateDriver` | `jina.drivers.evaluate` |
| `URI2Buffer` | `jina.drivers.convert` |
| `URI2DataURI` | `jina.drivers.convert` |
| `URI2Text` | `jina.drivers.convert` |
| `VectorFillDriver` |   |
| `VectorIndexDriver` | `jina.drivers.cache` |
| `VectorSearchDriver` |   |
| `WaitDriver` | `jina.drivers.control` |