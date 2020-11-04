# List of 66 Drivers in Jina

This version of Jina includes 66 Drivers.

## Inheritances in a Tree View
- `BaseDriver`
   - `BaseRecursiveDriver`
      - `QuerySetReader`
         - `SliceQL`
         - `ReverseQL`
         - `SortQL`
         - `ExcludeQL`
            - `ExcludeReqQL`
               - `SelectReqQL`
            - `SelectQL`
         - `FilterQL`
      - `BaseExecutableDriver`
         - `BaseEncodeDriver`
            - `MultiModalDriver`
            - `EncodeDriver`
         - `CraftDriver`
            - `SegmentDriver`
         - `BaseIndexDriver`
            - `KVIndexDriver`
            - `VectorIndexDriver`
            - `BaseCacheDriver`
               - `TaggingCacheDriver`
         - `BaseEvaluateDriver`
            - `FieldEvaluateDriver`
               - `NDArrayEvaluateDriver`
               - `RankEvaluateDriver`
               - `TextEvaluateDriver`
         - `BaseSearchDriver`
            - `KVSearchDriver`
               - `LoadGroundTruthDriver`
            - `QuerySetReader`
               - `VectorFillDriver`
               - `VectorSearchDriver`
         - `BasePredictDriver`
            - `BaseLabelPredictDriver`
               - `BinaryPredictDriver`
               - `OneHotPredictDriver`
                  - `MultiLabelPredictDriver`
            - `Prediction2DocBlobDriver`
         - `BaseRankDriver`
            - `Chunk2DocRankDriver`
            - `CollectMatches2DocRankDriver`
            - `Matches2DocRankDriver`
      - `ReduceDriver`
         - `ReduceAllDriver`
            - `CollectEvaluationDriver`
         - `ConcatEmbedDriver`
      - `BaseConvertDriver`
         - `URI2Buffer`
            - `URI2DataURI`
               - `Buffer2URI`
                  - `Text2URI`
                     - `All2URI`
               - `Text2URI`
            - `URI2Text`
         - `NdArray2PngURI`
            - `Blob2PngURI`
         - `Buffer2NdArray`
         - `MIMEDriver`
   - `ControlReqDriver`
      - `RouteDriver`
         - `ForwardDriver`
   - `LogInfoDriver`
   - `WaitDriver`
   - `BaseQueryLangDriver`
      - `CythonFilterDriver`
      - `GraphQLDriver`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `All2URI` |   |
| `BaseCacheDriver` | `jina.drivers.cache` |
| `BaseConvertDriver` | `jina.drivers.convert` |
| `BaseDriver` |   |
| `BaseEncodeDriver` | `jina.drivers.rank` |
| `BaseEvaluateDriver` | `jina.drivers.rank` |
| `BaseExecutableDriver` | `jina.drivers.convert` |
| `BaseIndexDriver` | `jina.drivers.rank` |
| `BaseLabelPredictDriver` | `jina.drivers.predict` |
| `BasePredictDriver` | `jina.drivers.rank` |
| `BaseQueryLangDriver` | `jina.drivers.querylang` |
| `BaseRankDriver` | `jina.drivers.rank` |
| `BaseRecursiveDriver` | `jina.drivers.querylang` |
| `BaseSearchDriver` | `jina.drivers.rank` |
| `BinaryPredictDriver` | `jina.drivers.predict` |
| `Blob2PngURI` | `jina.drivers.convert` |
| `Buffer2NdArray` | `jina.drivers.convert` |
| `Buffer2URI` | `jina.drivers.convert` |
| `Chunk2DocRankDriver` | `jina.drivers.rank` |
| `CollectEvaluationDriver` | `jina.drivers.reduce` |
| `CollectMatches2DocRankDriver` | `jina.drivers.rank` |
| `ConcatEmbedDriver` | `jina.drivers.reduce` |
| `ControlReqDriver` | `jina.drivers.querylang` |
| `CraftDriver` | `jina.drivers.rank` |
| `CythonFilterDriver` | `jina.drivers.querylang` |
| `EncodeDriver` | `jina.drivers.encode` |
| `ExcludeQL` |   |
| `ExcludeReqQL` | `jina.drivers.querylang.select` |
| `FieldEvaluateDriver` | `jina.drivers.evaluate` |
| `FilterQL` |   |
| `ForwardDriver` | `jina.drivers.control` |
| `GraphQLDriver` | `jina.drivers.querylang` |
| `KVIndexDriver` | `jina.drivers.cache` |
| `KVSearchDriver` | `jina.drivers.search` |
| `LoadGroundTruthDriver` | `jina.drivers.search` |
| `LogInfoDriver` | `jina.drivers.querylang` |
| `MIMEDriver` | `jina.drivers.convert` |
| `Matches2DocRankDriver` | `jina.drivers.rank` |
| `MultiLabelPredictDriver` | `jina.drivers.predict` |
| `MultiModalDriver` | `jina.drivers.encode` |
| `NDArrayEvaluateDriver` | `jina.drivers.evaluate` |
| `NdArray2PngURI` | `jina.drivers.convert` |
| `OneHotPredictDriver` | `jina.drivers.predict` |
| `Prediction2DocBlobDriver` | `jina.drivers.predict` |
| `QuerySetReader` | `jina.drivers.convert` |
| `QuerySetReader` | `jina.drivers.search` |
| `RankEvaluateDriver` | `jina.drivers.evaluate` |
| `ReduceAllDriver` | `jina.drivers.reduce` |
| `ReduceDriver` | `jina.drivers.convert` |
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
| `WaitDriver` | `jina.drivers.querylang` |