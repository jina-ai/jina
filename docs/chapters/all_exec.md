# List of 60 Executors in Jina

This version of Jina includes 60 Executors.

## Inheritances in a Tree View
- `BaseExecutor`
   - `BaseEncoder`
      - `BaseNumericEncoder`
         - `BaseImageEncoder`
            - `OnnxImageEncoder`
            - `KerasImageEncoder`
         - `PaddlehubEncoder`
            - `ImagePaddlehubEncoder`
            - `VideoPaddlehubEncoder`
         - `BaseAudioEncoder`
         - `BaseVideoEncoder`
         - `TorchEncoder`
            - `VideoTorchEncoder`
            - `ImageTorchEncoder`
         - `IncrementalPCAEncoder`
      - `BaseTextEncoder`
         - `OneHotTextEncoder`
         - `TransformerEncoder`
            - `TransformerTFEncoder`
            - `TransformerTorchEncoder`
         - `TextPaddlehubEncoder`
         - `FlairTextEncoder`
   - `CompoundExecutor`
      - `PipelineEncoder`
      - `ChunkIndexer`
   - `BaseIndexer`
      - `BaseKVIndexer`
         - `BasePbIndexer`
            - `LeveldbIndexer`
               - `ChunkLeveldbIndexer`
               - `DocLeveldbIndexer`
            - `ChunkPbIndexer`
            - `DocPbIndexer`
      - `BaseVectorIndexer`
         - `NumpyIndexer`
            - `SptagIndexer`
            - `AnnoyIndexer`
            - `FaissIndexer`
            - `NmslibIndexer`
   - `BaseCrafter`
      - `BaseChunkCrafter`
         - `ImageChunkCrafter`
            - `ImageResizer`
            - `ImageNormalizer`
            - `CenterImageCropper`
            - `FiveImageCropper`
            - `ImageCropper`
            - `RandomImageCropper`
            - `SlidingWindowImageCropper`
      - `BaseSegmenter`
         - `JiebaSegmenter`
         - `Sentencizer`
         - `ImageReader`
      - `BaseDocCrafter`
   - `BaseRanker`
      - `MaxRanker`
      - `MinRanker`
      - `BiMatchRanker`
      - `TfIdfRanker`
         - `BM25Ranker`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `AnnoyIndexer` | `jina.executors.indexers.vector.nmslib` |
| `BM25Ranker` | `jina.executors.rankers.tfidf` |
| `BaseAudioEncoder` | `jina.executors.encoders.torchvision` |
| `BaseChunkCrafter` | `jina.executors.crafters` |
| `BaseCrafter` | `jina.executors.compound` |
| `BaseDocCrafter` | `jina.executors.crafters` |
| `BaseEncoder` | `jina.executors.compound` |
| `BaseExecutor` |   |
| `BaseImageEncoder` | `jina.executors.encoders.torchvision` |
| `BaseIndexer` | `jina.executors.compound` |
| `BaseKVIndexer` | `jina.executors.indexers` |
| `BaseNumericEncoder` | `jina.executors.encoders` |
| `BasePbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `BaseRanker` | `jina.executors.compound` |
| `BaseSegmenter` | `jina.executors.crafters` |
| `BaseTextEncoder` | `jina.executors.encoders` |
| `BaseVectorIndexer` | `jina.executors.indexers` |
| `BaseVideoEncoder` | `jina.executors.encoders.torchvision` |
| `BiMatchRanker` | `jina.executors.rankers.tfidf` |
| `CenterImageCropper` | `jina.executors.crafters.image` |
| `ChunkIndexer` | `jina.executors.compound` |
| `ChunkLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `ChunkPbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `CompoundExecutor` | `jina.executors.compound` |
| `DocLeveldbIndexer` | `jina.executors.indexers.keyvalue.leveldb` |
| `DocPbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `FaissIndexer` | `jina.executors.indexers.vector.nmslib` |
| `FiveImageCropper` | `jina.executors.crafters.image` |
| `FlairTextEncoder` | `jina.executors.encoders.nlp.flair` |
| `ImageChunkCrafter` | `jina.executors.crafters` |
| `ImageCropper` | `jina.executors.crafters.image` |
| `ImageNormalizer` | `jina.executors.crafters.image` |
| `ImagePaddlehubEncoder` | `jina.executors.encoders.video.paddlehub` |
| `ImageReader` | `jina.executors.crafters` |
| `ImageResizer` | `jina.executors.crafters.image` |
| `ImageTorchEncoder` | `jina.executors.encoders.image.torchvision` |
| `IncrementalPCAEncoder` | `jina.executors.encoders.torchvision` |
| `JiebaSegmenter` | `jina.executors.crafters` |
| `KerasImageEncoder` | `jina.executors.encoders.image.tfkeras` |
| `LeveldbIndexer` | `jina.executors.indexers.keyvalue.proto` |
| `MaxRanker` | `jina.executors.rankers.tfidf` |
| `MinRanker` | `jina.executors.rankers.tfidf` |
| `NmslibIndexer` | `jina.executors.indexers.vector.nmslib` |
| `NumpyIndexer` | `jina.executors.indexers.vector.numpy` |
| `OneHotTextEncoder` | `jina.executors.encoders.nlp.flair` |
| `OnnxImageEncoder` | `jina.executors.encoders.image.tfkeras` |
| `PaddlehubEncoder` | `jina.executors.encoders.torchvision` |
| `PipelineEncoder` | `jina.executors.compound` |
| `RandomImageCropper` | `jina.executors.crafters.image` |
| `Sentencizer` | `jina.executors.crafters` |
| `SlidingWindowImageCropper` | `jina.executors.crafters.image` |
| `SptagIndexer` | `jina.executors.indexers.vector.nmslib` |
| `TextPaddlehubEncoder` | `jina.executors.encoders.nlp.flair` |
| `TfIdfRanker` | `jina.executors.rankers.tfidf` |
| `TorchEncoder` | `jina.executors.encoders.torchvision` |
| `TransformerEncoder` | `jina.executors.encoders.nlp.flair` |
| `TransformerTFEncoder` | `jina.executors.encoders.nlp.transformer` |
| `TransformerTorchEncoder` | `jina.executors.encoders.nlp.transformer` |
| `VideoPaddlehubEncoder` | `jina.executors.encoders.video.paddlehub` |
| `VideoTorchEncoder` | `jina.executors.encoders.image.torchvision` |