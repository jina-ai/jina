# List of 72 Executors in Jina

This version of Jina includes 72 Executors.

## Inheritances in a Tree View
- `BaseExecutor`
   - `BaseFrameworkExecutor`
      - `BaseTorchExecutor`
         - `BaseTorchEncoder`
            - `VideoTorchEncoder`
            - `ImageTorchEncoder`
         - `BaseTransformerEncoder`
            - `TransformerTorchEncoder`
      - `BaseOnnxExecutor`
         - `BaseOnnxEncoder`
            - `OnnxImageEncoder`
      - `BasePaddleExecutor`
      - `BaseTFExecutor`
         - `BaseTransformerEncoder`
            - `TransformerTFEncoder`
      - `BaseTransformerEncoder`
   - `BaseRanker`
      - `TfIdfRanker`
         - `BM25Ranker`
      - `MaxRanker`
      - `MinRanker`
      - `BiMatchRanker`
   - `BaseEncoder`
      - `BaseTextEncoder`
         - `BaseFrameworkExecutor`
            - `BaseTorchExecutor`
               - `FarmTextEncoder`
               - `FlairTextEncoder`
            - `BasePaddleExecutor`
               - `TextPaddlehubEncoder`
         - `OneHotTextEncoder`
      - `BaseNumericEncoder`
         - `BaseFrameworkExecutor`
            - `BasePaddleExecutor`
               - `BaseCVPaddlehubEncoder`
                  - `VideoPaddlehubEncoder`
                  - `ImagePaddlehubEncoder`
         - `BaseImageEncoder`
            - `BaseFrameworkExecutor`
               - `BaseTFExecutor`
                  - `KerasImageEncoder`
         - `BaseAudioEncoder`
         - `BaseVideoEncoder`
         - `IncrementalPCAEncoder`
   - `BaseIndexer`
      - `BaseKVIndexer`
         - `BasePbIndexer`
            - `ChunkPbIndexer`
            - `DocPbIndexer`
            - `LeveldbIndexer`
               - `ChunkLeveldbIndexer`
               - `DocLeveldbIndexer`
      - `BaseVectorIndexer`
         - `NumpyIndexer`
            - `SptagIndexer`
            - `NmslibIndexer`
            - `AnnoyIndexer`
            - `FaissIndexer`
   - `CompoundExecutor`
      - `ChunkIndexer`
      - `PipelineEncoder`
   - `BaseCrafter`
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
      - `BaseSegmenter`
         - `JiebaSegmenter`
         - `Sentencizer`
         - `ImageReader`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `AnnoyIndexer` | `jina.executors.indexers.vector.faiss` |
| `BM25Ranker` | `jina.executors.rankers.tfidf` |
| `BaseAudioEncoder` | `jina.executors.encoders.numeric.pca` |
| `BaseCVPaddlehubEncoder` |   |
| `BaseChunkCrafter` | `jina.executors.crafters` |
| `BaseCrafter` | `jina.executors.encoders` |
| `BaseDocCrafter` | `jina.executors.crafters` |
| `BaseEncoder` | `jina.executors.encoders` |
| `BaseExecutor` |   |
| `BaseFrameworkExecutor` | `jina.executors.encoders.nlp.char` |
| `BaseFrameworkExecutor` | `jina.executors.encoders.numeric.pca` |
| `BaseFrameworkExecutor` | `jina.executors.encoders` |
| `BaseImageEncoder` | `jina.executors.encoders.numeric.pca` |
| `BaseIndexer` | `jina.executors.encoders` |
| `BaseKVIndexer` | `jina.executors.indexers` |
| `BaseNumericEncoder` | `jina.executors.encoders` |
| `BaseOnnxEncoder` | `jina.executors.encoders.frameworks` |
| `BaseOnnxExecutor` | `jina.executors.encoders.nlp.transformer` |
| `BasePaddleExecutor` |   |
| `BasePaddleExecutor` | `jina.executors.encoders.nlp.transformer` |
| `BasePbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `BaseRanker` | `jina.executors.encoders` |
| `BaseSegmenter` | `jina.executors.crafters` |
| `BaseTFExecutor` |   |
| `BaseTFExecutor` | `jina.executors.encoders.nlp.transformer` |
| `BaseTextEncoder` | `jina.executors.encoders` |
| `BaseTorchEncoder` | `jina.executors.encoders.nlp.transformer` |
| `BaseTorchExecutor` |   |
| `BaseTorchExecutor` | `jina.executors.encoders.nlp.transformer` |
| `BaseTransformerEncoder` | `jina.executors.encoders.nlp.transformer` |
| `BaseVectorIndexer` | `jina.executors.indexers` |
| `BaseVideoEncoder` | `jina.executors.encoders.numeric.pca` |
| `BiMatchRanker` | `jina.executors.rankers.bi_match` |
| `CenterImageCropper` | `jina.executors.crafters.image.normalize` |
| `ChunkIndexer` | `jina.executors.encoders` |
| `ChunkLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `ChunkPbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `CompoundExecutor` | `jina.executors.encoders` |
| `DocLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `DocPbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `FaissIndexer` | `jina.executors.indexers.vector.faiss` |
| `FarmTextEncoder` |   |
| `FiveImageCropper` | `jina.executors.crafters.image.normalize` |
| `FlairTextEncoder` |   |
| `ImageChunkCrafter` | `jina.executors.crafters.image` |
| `ImageCropper` | `jina.executors.crafters.image.normalize` |
| `ImageNormalizer` | `jina.executors.crafters.image.normalize` |
| `ImagePaddlehubEncoder` | `jina.executors.encoders.image.paddlehub` |
| `ImageReader` | `jina.executors.crafters.image.io` |
| `ImageResizer` | `jina.executors.crafters.image.normalize` |
| `ImageTorchEncoder` | `jina.executors.encoders.image.torchvision` |
| `IncrementalPCAEncoder` | `jina.executors.encoders.numeric.pca` |
| `JiebaSegmenter` | `jina.executors.crafters.image.io` |
| `KerasImageEncoder` |   |
| `LeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `MaxRanker` | `jina.executors.rankers.bi_match` |
| `MinRanker` | `jina.executors.rankers.bi_match` |
| `NmslibIndexer` | `jina.executors.indexers.vector.faiss` |
| `NumpyIndexer` | `jina.executors.indexers.vector.numpy` |
| `OneHotTextEncoder` | `jina.executors.encoders.nlp.char` |
| `OnnxImageEncoder` | `jina.executors.encoders.frameworks` |
| `PipelineEncoder` | `jina.executors.encoders` |
| `RandomImageCropper` | `jina.executors.crafters.image.normalize` |
| `Sentencizer` | `jina.executors.crafters.image.io` |
| `SlidingWindowImageCropper` | `jina.executors.crafters.image.normalize` |
| `SptagIndexer` | `jina.executors.indexers.vector.faiss` |
| `TextPaddlehubEncoder` |   |
| `TfIdfRanker` | `jina.executors.rankers.bi_match` |
| `TransformerTFEncoder` |   |
| `TransformerTorchEncoder` |   |
| `VideoPaddlehubEncoder` | `jina.executors.encoders.image.paddlehub` |
| `VideoTorchEncoder` | `jina.executors.encoders.image.torchvision` |