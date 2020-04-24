# List of 57 Executors in Jina

This version of Jina includes 57 Executors.

## Inheritances in a Tree View
- `BaseExecutor`
   - `BaseRanker`
      - `BiMatchRanker`
      - `TfIdfRanker`
         - `BM25Ranker`
   - `BaseCrafter`
      - `BaseChunkCrafter`
         - `ImageChunkCrafter`
            - `CenterImageCropper`
            - `FiveImageCropper`
            - `ImageCropper`
            - `RandomImageCropper`
            - `SlidingWindowImageCropper`
            - `ImageResizer`
            - `ImageNormalizer`
      - `BaseSegmenter`
         - `Sentencizer`
         - `ImageReader`
      - `BaseDocCrafter`
   - `BaseEncoder`
      - `BaseNumericEncoder`
         - `PaddlehubEncoder`
            - `ImagePaddlehubEncoder`
            - `VideoPaddlehubEncoder`
         - `IncrementalPCAEncoder`
         - `TorchEncoder`
            - `ImageTorchEncoder`
            - `VideoTorchEncoder`
         - `BaseAudioEncoder`
         - `BaseImageEncoder`
            - `OnnxImageEncoder`
            - `KerasImageEncoder`
         - `BaseVideoEncoder`
      - `BaseTextEncoder`
         - `TextPaddlehubEncoder`
         - `FlairTextEncoder`
         - `TransformerEncoder`
            - `TransformerTFEncoder`
            - `TransformerTorchEncoder`
         - `OneHotTextEncoder`
   - `CompoundExecutor`
      - `PipelineEncoder`
      - `ChunkIndexer`
   - `BaseIndexer`
      - `BaseVectorIndexer`
         - `NumpyIndexer`
            - `SptagIndexer`
            - `AnnoyIndexer`
            - `NmslibIndexer`
            - `FaissIndexer`
      - `BaseKVIndexer`
         - `BasePbIndexer`
            - `ChunkPbIndexer`
            - `DocPbIndexer`
            - `LeveldbIndexer`
               - `ChunkLeveldbIndexer`
               - `DocLeveldbIndexer`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `AnnoyIndexer` | `jina.executors.indexers.vector.faiss` |
| `BM25Ranker` | `jina.executors.rankers.tfidf` |
| `BaseAudioEncoder` | `jina.executors.encoders.torchvision` |
| `BaseChunkCrafter` | `jina.executors.crafters` |
| `BaseCrafter` | `jina.executors.indexers` |
| `BaseDocCrafter` | `jina.executors.crafters` |
| `BaseEncoder` | `jina.executors.indexers` |
| `BaseExecutor` |   |
| `BaseImageEncoder` | `jina.executors.encoders.torchvision` |
| `BaseIndexer` | `jina.executors.indexers` |
| `BaseKVIndexer` | `jina.executors.indexers` |
| `BaseNumericEncoder` | `jina.executors.encoders` |
| `BasePbIndexer` | `jina.executors.indexers` |
| `BaseRanker` | `jina.executors.indexers` |
| `BaseSegmenter` | `jina.executors.crafters` |
| `BaseTextEncoder` | `jina.executors.encoders` |
| `BaseVectorIndexer` | `jina.executors.indexers` |
| `BaseVideoEncoder` | `jina.executors.encoders.torchvision` |
| `BiMatchRanker` | `jina.executors.rankers.tfidf` |
| `CenterImageCropper` | `jina.executors.crafters.image` |
| `ChunkIndexer` | `jina.executors.indexers` |
| `ChunkLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `ChunkPbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `CompoundExecutor` | `jina.executors.indexers` |
| `DocLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `DocPbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `FaissIndexer` | `jina.executors.indexers.vector.faiss` |
| `FiveImageCropper` | `jina.executors.crafters.image` |
| `FlairTextEncoder` | `jina.executors.encoders.nlp.char` |
| `ImageChunkCrafter` | `jina.executors.crafters.image` |
| `ImageCropper` | `jina.executors.crafters.image` |
| `ImageNormalizer` | `jina.executors.crafters.image` |
| `ImagePaddlehubEncoder` | `jina.executors.encoders.paddlehub` |
| `ImageReader` | `jina.executors.crafters.image.io` |
| `ImageResizer` | `jina.executors.crafters.image` |
| `ImageTorchEncoder` | `jina.executors.encoders.torchvision` |
| `IncrementalPCAEncoder` | `jina.executors.encoders.torchvision` |
| `KerasImageEncoder` | `jina.executors.encoders.image.tfkeras` |
| `LeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `NmslibIndexer` | `jina.executors.indexers.vector.faiss` |
| `NumpyIndexer` | `jina.executors.indexers` |
| `OneHotTextEncoder` | `jina.executors.encoders.nlp.char` |
| `OnnxImageEncoder` | `jina.executors.encoders.image.tfkeras` |
| `PaddlehubEncoder` | `jina.executors.encoders.torchvision` |
| `PipelineEncoder` | `jina.executors.indexers` |
| `RandomImageCropper` | `jina.executors.crafters.image` |
| `Sentencizer` | `jina.executors.crafters.image.io` |
| `SlidingWindowImageCropper` | `jina.executors.crafters.image` |
| `SptagIndexer` | `jina.executors.indexers.vector.faiss` |
| `TextPaddlehubEncoder` | `jina.executors.encoders.nlp.char` |
| `TfIdfRanker` | `jina.executors.rankers.tfidf` |
| `TorchEncoder` | `jina.executors.encoders.torchvision` |
| `TransformerEncoder` | `jina.executors.encoders.nlp.char` |
| `TransformerTFEncoder` | `jina.executors.encoders.nlp.transformer` |
| `TransformerTorchEncoder` | `jina.executors.encoders.nlp.transformer` |
| `VideoPaddlehubEncoder` | `jina.executors.encoders.paddlehub` |
| `VideoTorchEncoder` | `jina.executors.encoders.torchvision` |