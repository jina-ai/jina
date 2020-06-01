# List of 80 Executors in Jina

This version of Jina includes 80 Executors.

## Inheritances in a Tree View
- `BaseExecutor`
   - `BaseIndexer`
      - `BaseVectorIndexer`
         - `NumpyIndexer`
            - `SptagIndexer`
            - `FaissIndexer`
            - `AnnoyIndexer`
            - `NmslibIndexer`
      - `BaseKVIndexer`
         - `BasePbIndexer`
            - `ChunkPbIndexer`
            - `DocPbIndexer`
            - `LeveldbIndexer`
               - `ChunkLeveldbIndexer`
               - `DocLeveldbIndexer`
   - `BaseCrafter`
      - `BaseSegmenter`
         - `JiebaSegmenter`
         - `Sentencizer`
         - `ImageReader`
      - `BaseChunkCrafter`
         - `ImageChunkCrafter`
            - `ImageResizer`
            - `CenterImageCropper`
            - `FiveImageCropper`
            - `ImageCropper`
            - `RandomImageCropper`
            - `SlidingWindowImageCropper`
            - `ImageNormalizer`
      - `BaseDocCrafter`
   - `BaseEncoder`
      - `BaseFrameworkExecutor`
         - `BasePaddleExecutor`
            - `BasePaddlehubEncoder`
               - `BaseTextPaddlehubEncoder`
                  - `TextPaddlehubEncoder`
               - `BaseCVPaddlehubEncoder`
                  - `ImagePaddlehubEncoder`
                  - `VideoPaddlehubEncoder`
         - `BaseTFExecutor`
            - `BaseTFEncoder`
               - `BaseCVTFEncoder`
                  - `KerasImageEncoder`
               - `BaseTextTFEncoder`
                  - `BaseTransformerEncoder`
                     - `TransformerTFEncoder`
         - `BaseTorchExecutor`
            - `BaseTorchEncoder`
               - `BaseTextTorchEncoder`
                  - `FarmTextEncoder`
                  - `FlairTextEncoder`
                  - `BaseTransformerEncoder`
                     - `TransformerTorchEncoder`
               - `BaseCVTorchEncoder`
                  - `ImageTorchEncoder`
         - `BaseOnnxExecutor`
            - `BaseOnnxEncoder`
               - `OnnxImageEncoder`
      - `BaseTextEncoder`
         - `OneHotTextEncoder`
      - `BaseNumericEncoder`
         - `BaseVideoEncoder`
            - `BaseFrameworkExecutor`
               - `BaseTorchExecutor`
                  - `BaseTorchEncoder`
                     - `BaseCVTorchEncoder`
                        - `VideoTorchEncoder`
         - `IncrementalPCAEncoder`
         - `BaseAudioEncoder`
         - `BaseImageEncoder`
      - `BaseTransformerEncoder`
   - `Chunk2DocRanker`
      - `MaxRanker`
      - `MinRanker`
      - `TfIdfRanker`
         - `BM25Ranker`
      - `BiMatchRanker`
   - `CompoundExecutor`
      - `ChunkIndexer`
      - `PipelineEncoder`
   - `BaseFrameworkExecutor`
      - `BaseOnnxExecutor`
      - `BasePaddleExecutor`
      - `BaseTFExecutor`
      - `BaseTorchExecutor`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `AnnoyIndexer` | `jina.executors.indexers.vector.nmslib` |
| `BM25Ranker` | `jina.executors.rankers.tfidf` |
| `BaseAudioEncoder` | `jina.executors.encoders` |
| `BaseCVPaddlehubEncoder` | `jina.executors.encoders.frameworks` |
| `BaseCVTFEncoder` | `jina.executors.encoders.frameworks` |
| `BaseCVTorchEncoder` |   |
| `BaseCVTorchEncoder` | `jina.executors.encoders.frameworks` |
| `BaseChunkCrafter` | `jina.executors.crafters` |
| `BaseCrafter` | `jina.executors.encoders` |
| `BaseDocCrafter` | `jina.executors.crafters` |
| `BaseEncoder` | `jina.executors.encoders` |
| `BaseExecutor` |   |
| `BaseFrameworkExecutor` | `jina.executors.encoders` |
| `BaseImageEncoder` | `jina.executors.encoders` |
| `BaseIndexer` | `jina.executors.encoders` |
| `BaseKVIndexer` | `jina.executors.indexers` |
| `BaseNumericEncoder` | `jina.executors.encoders` |
| `BaseOnnxEncoder` |   |
| `BaseOnnxExecutor` |   |
| `BaseOnnxExecutor` | `jina.executors.frameworks` |
| `BasePaddleExecutor` |   |
| `BasePaddleExecutor` | `jina.executors.frameworks` |
| `BasePaddlehubEncoder` |   |
| `BasePbIndexer` | `jina.executors.indexers` |
| `Chunk2DocRanker` | `jina.executors.encoders` |
| `BaseSegmenter` | `jina.executors.crafters` |
| `BaseTFEncoder` |   |
| `BaseTFExecutor` |   |
| `BaseTFExecutor` | `jina.executors.frameworks` |
| `BaseTextEncoder` | `jina.executors.encoders` |
| `BaseTextPaddlehubEncoder` | `jina.executors.encoders.frameworks` |
| `BaseTextTFEncoder` | `jina.executors.encoders.frameworks` |
| `BaseTextTorchEncoder` | `jina.executors.encoders.frameworks` |
| `BaseTorchEncoder` |   |
| `BaseTorchExecutor` |   |
| `BaseTorchExecutor` | `jina.executors.frameworks` |
| `BaseTransformerEncoder` | `jina.executors.encoders.nlp.transformer` |
| `BaseTransformerEncoder` | `jina.executors.encoders` |
| `BaseVectorIndexer` | `jina.executors.indexers` |
| `BaseVideoEncoder` | `jina.executors.encoders` |
| `BiMatchRanker` | `jina.executors.rankers.bi_match` |
| `CenterImageCropper` | `jina.executors.crafters.image` |
| `ChunkIndexer` | `jina.executors.encoders` |
| `ChunkLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `ChunkPbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `CompoundExecutor` | `jina.executors.encoders` |
| `DocLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `DocPbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `FaissIndexer` | `jina.executors.indexers.vector.nmslib` |
| `FarmTextEncoder` | `jina.executors.encoders.nlp.transformer` |
| `FiveImageCropper` | `jina.executors.crafters.image` |
| `FlairTextEncoder` | `jina.executors.encoders.nlp.transformer` |
| `ImageChunkCrafter` | `jina.executors.crafters` |
| `ImageCropper` | `jina.executors.crafters.image` |
| `ImageNormalizer` | `jina.executors.crafters.image` |
| `ImagePaddlehubEncoder` | `jina.executors.encoders.frameworks` |
| `ImageReader` | `jina.executors.crafters` |
| `ImageResizer` | `jina.executors.crafters.image` |
| `ImageTorchEncoder` | `jina.executors.encoders.frameworks` |
| `IncrementalPCAEncoder` | `jina.executors.encoders` |
| `JiebaSegmenter` | `jina.executors.crafters` |
| `KerasImageEncoder` | `jina.executors.encoders.frameworks` |
| `LeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `MaxRanker` | `jina.executors.rankers.bi_match` |
| `MinRanker` | `jina.executors.rankers.bi_match` |
| `NmslibIndexer` | `jina.executors.indexers.vector.nmslib` |
| `NumpyIndexer` | `jina.executors.indexers.vector.numpy` |
| `OneHotTextEncoder` | `jina.executors.encoders` |
| `OnnxImageEncoder` | `jina.executors.encoders.frameworks` |
| `PipelineEncoder` | `jina.executors.encoders` |
| `RandomImageCropper` | `jina.executors.crafters.image` |
| `Sentencizer` | `jina.executors.crafters` |
| `SlidingWindowImageCropper` | `jina.executors.crafters.image` |
| `SptagIndexer` | `jina.executors.indexers.vector.nmslib` |
| `TextPaddlehubEncoder` | `jina.executors.encoders.frameworks` |
| `TfIdfRanker` | `jina.executors.rankers.bi_match` |
| `TransformerTFEncoder` |   |
| `TransformerTorchEncoder` |   |
| `VideoPaddlehubEncoder` | `jina.executors.encoders.frameworks` |
| `VideoTorchEncoder` |   |