# List of 57 Executors in Jina

This version of Jina includes 57 Executors.

#### Tree View
- `BaseExecutor`
   - `BaseIndexer`
      - `BaseVectorIndexer`
         - `NumpyIndexer`
            - `AnnoyIndexer`
            - `NmslibIndexer`
            - `SptagIndexer`
            - `FaissIndexer`
      - `BaseKVIndexer`
         - `BasePbIndexer`
            - `LeveldbIndexer`
               - `ChunkLeveldbIndexer`
               - `DocLeveldbIndexer`
            - `ChunkPbIndexer`
            - `DocPbIndexer`
   - `BaseCrafter`
      - `BaseSegmenter`
         - `ImageReader`
         - `Sentencizer`
      - `BaseChunkCrafter`
         - `ImageChunkCrafter`
            - `CenterImageCropper`
            - `FiveImageCropper`
            - `ImageCropper`
            - `RandomImageCropper`
            - `SlidingWindowImageCropper`
            - `ImageNormalizer`
            - `ImageResizer`
      - `BaseDocCrafter`
   - `BaseEncoder`
      - `BaseNumericEncoder`
         - `BaseImageEncoder`
            - `KerasImageEncoder`
            - `OnnxImageEncoder`
         - `PaddlehubEncoder`
            - `VideoPaddlehubEncoder`
            - `ImagePaddlehubEncoder`
         - `TorchEncoder`
            - `VideoTorchEncoder`
            - `ImageTorchEncoder`
         - `IncrementalPCAEncoder`
         - `BaseAudioEncoder`
         - `BaseVideoEncoder`
      - `BaseTextEncoder`
         - `TextPaddlehubEncoder`
         - `FlairTextEncoder`
         - `OneHotTextEncoder`
         - `TransformerEncoder`
            - `TransformerTFEncoder`
            - `TransformerTorchEncoder`
   - `CompoundExecutor`
      - `ChunkIndexer`
      - `PipelineEncoder`
   - `BaseRanker`
      - `BiMatchRanker`
      - `TfIdfRanker`
         - `BM25Ranker`

### Table View 

| Class | Module |
| --- | --- |
| `AnnoyIndexer` | `jina.executors.indexers.vector.numpy` |
| `BM25Ranker` | `jina.executors.rankers.tfidf` |
| `BaseAudioEncoder` | `jina.executors.encoders.torchvision` |
| `BaseChunkCrafter` | `jina.executors.crafters` |
| `BaseCrafter` | `jina.executors.encoders` |
| `BaseDocCrafter` | `jina.executors.crafters` |
| `BaseEncoder` | `jina.executors.encoders` |
| `BaseExecutor` |   |
| `BaseImageEncoder` | `jina.executors.encoders.torchvision` |
| `BaseIndexer` | `jina.executors.encoders` |
| `BaseKVIndexer` | `jina.executors.indexers` |
| `BaseNumericEncoder` | `jina.executors.encoders` |
| `BasePbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `BaseRanker` | `jina.executors.encoders` |
| `BaseSegmenter` | `jina.executors.crafters` |
| `BaseTextEncoder` | `jina.executors.encoders` |
| `BaseVectorIndexer` | `jina.executors.indexers` |
| `BaseVideoEncoder` | `jina.executors.encoders.torchvision` |
| `BiMatchRanker` | `jina.executors.rankers.tfidf` |
| `CenterImageCropper` | `jina.executors.crafters.image` |
| `ChunkIndexer` | `jina.executors.encoders` |
| `ChunkLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `ChunkPbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `CompoundExecutor` | `jina.executors.encoders` |
| `DocLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `DocPbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `FaissIndexer` | `jina.executors.indexers.vector.numpy` |
| `FiveImageCropper` | `jina.executors.crafters.image` |
| `FlairTextEncoder` | `jina.executors.encoders` |
| `ImageChunkCrafter` | `jina.executors.crafters.image` |
| `ImageCropper` | `jina.executors.crafters.image` |
| `ImageNormalizer` | `jina.executors.crafters.image` |
| `ImagePaddlehubEncoder` | `jina.executors.encoders.paddlehub` |
| `ImageReader` | `jina.executors.crafters` |
| `ImageResizer` | `jina.executors.crafters.image` |
| `ImageTorchEncoder` | `jina.executors.encoders.torchvision` |
| `IncrementalPCAEncoder` | `jina.executors.encoders.torchvision` |
| `KerasImageEncoder` | `jina.executors.encoders.image.onnx` |
| `LeveldbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `NmslibIndexer` | `jina.executors.indexers.vector.numpy` |
| `NumpyIndexer` | `jina.executors.indexers.vector.numpy` |
| `OneHotTextEncoder` | `jina.executors.encoders` |
| `OnnxImageEncoder` | `jina.executors.encoders.image.onnx` |
| `PaddlehubEncoder` | `jina.executors.encoders.torchvision` |
| `PipelineEncoder` | `jina.executors.encoders` |
| `RandomImageCropper` | `jina.executors.crafters.image` |
| `Sentencizer` | `jina.executors.crafters` |
| `SlidingWindowImageCropper` | `jina.executors.crafters.image` |
| `SptagIndexer` | `jina.executors.indexers.vector.numpy` |
| `TextPaddlehubEncoder` | `jina.executors.encoders` |
| `TfIdfRanker` | `jina.executors.rankers.tfidf` |
| `TorchEncoder` | `jina.executors.encoders.torchvision` |
| `TransformerEncoder` | `jina.executors.encoders` |
| `TransformerTFEncoder` | `jina.executors.encoders.nlp.transformer` |
| `TransformerTorchEncoder` | `jina.executors.encoders.nlp.transformer` |
| `VideoPaddlehubEncoder` | `jina.executors.encoders.paddlehub` |
| `VideoTorchEncoder` | `jina.executors.encoders.torchvision` |