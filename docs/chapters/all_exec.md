# List of 100 Executors in Jina

This version of Jina includes 100 Executors.

## Inheritances in a Tree View
- `BaseExecutor`
   - `BaseCrafter`
      - `ArrayStringReader`
      - `ImageResizer`
      - `BaseSegmenter`
         - `BaseDevice`
            - `TorchDevice`
               - `TorchObjectDetectionSegmenter`
         - `SlidingWindowImageCropper`
         - `DeepSegmenter`
         - `SlidingWindowSegmenter`
         - `JiebaSegmenter`
         - `AudioSlicer`
         - `SlidingWindowAudioSlicer`
         - `FiveImageCropper`
         - `Sentencizer`
         - `PDFExtractorSegmenter`
         - `RandomImageCropper`
      - `ImageCropper`
      - `AudioReader`
      - `ArrayBytesReader`
      - `ImageFlipper`
      - `AudioMonophoner`
      - `TikaExtractor`
      - `CenterImageCropper`
      - `ImageReader`
      - `ImageNormalizer`
      - `AudioNormalizer`
   - `BaseIndexer`
      - `BaseVectorIndexer`
         - `BaseNumpyIndexer`
            - `AnnoyIndexer`
            - `ScannIndexer`
            - `BaseDevice`
               - `FaissDevice`
                  - `FaissIndexer`
            - `NGTIndexer`
            - `NumpyIndexer`
               - `ZarrIndexer`
            - `SptagIndexer`
            - `NmsLibIndexer`
         - `MilvusIndexer`
      - `BaseKVIndexer`
         - `BinaryPbIndexer`
            - `RedisDBIndexer`
            - `LevelDBIndexer`
            - `MongoDBIndexer`
   - `BaseEncoder`
      - `BaseDevice`
         - `PaddleDevice`
            - `BasePaddleEncoder`
               - `ImagePaddlehubEncoder`
               - `VideoPaddleEncoder`
               - `TextPaddlehubEncoder`
         - `TorchDevice`
            - `BaseTorchEncoder`
               - `ImageTorchEncoder`
               - `LaserEncoder`
               - `FlairTextEncoder`
               - `CustomImageTorchEncoder`
               - `FarmTextEncoder`
            - `TransformerTorchEncoder`
         - `TFDevice`
            - `BaseTFEncoder`
               - `ImageKerasEncoder`
               - `BigTransferEncoder`
               - `CustomKerasImageEncoder`
               - `UniversalSentenceEncoder`
               - `BaseNumericEncoder`
                  - `CompressionVaeEncoder`
            - `TransformerTFEncoder`
         - `OnnxDevice`
            - `BaseOnnxEncoder`
               - `ImageOnnxEncoder`
      - `BaseNumericEncoder`
         - `BaseVideoEncoder`
            - `BaseDevice`
               - `TorchDevice`
                  - `BaseTorchEncoder`
                     - `VideoTorchEncoder`
         - `TransformEncoder`
            - `FastICAEncoder`
            - `IncrementalPCAEncoder`
            - `RandomSparseEncoder`
            - `RandomGaussianEncoder`
            - `FeatureAgglomerationEncoder`
         - `TSNEEncoder`
         - `BaseAudioEncoder`
            - `BaseDevice`
               - `TorchDevice`
                  - `BaseTorchEncoder`
                     - `Wav2VecSpeechEncoder`
            - `ChromaPitchEncoder`
            - `MFCCTimbreEncoder`
      - `BaseTextEncoder`
         - `OneHotTextEncoder`
   - `BaseRanker`
      - `Chunk2DocRanker`
         - `BiMatchRanker`
         - `BM25Ranker`
         - `MinRanker`
         - `MaxRanker`
         - `TfIdfRanker`
      - `Match2DocRanker`
         - `LevenshteinRanker`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `AnnoyIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `ArrayBytesReader` | `jina.hub.crafters.audio.AudioNormalizer` |
| `ArrayStringReader` | `jina.hub.crafters.audio.AudioNormalizer` |
| `AudioMonophoner` | `jina.hub.crafters.audio.AudioNormalizer` |
| `AudioNormalizer` | `jina.hub.crafters.audio.AudioNormalizer` |
| `AudioReader` | `jina.hub.crafters.audio.AudioNormalizer` |
| `AudioSlicer` | `jina.hub.crafters.image.RandomImageCropper` |
| `BM25Ranker` | `jina.hub.rankers.TfIdfRanker` |
| `BaseAudioEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `BaseCrafter` |   |
| `BaseDevice` | `jina.hub.crafters.image.RandomImageCropper` |
| `BaseDevice` | `jina.hub.encoders.audio.MFCCTimbreEncoder` |
| `BaseDevice` | `jina.hub.encoders.nlp.TransformerTFEncoder` |
| `BaseDevice` | `jina.hub.encoders.video.VideoTorchEncoder` |
| `BaseDevice` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `BaseEncoder` |   |
| `BaseExecutor` |   |
| `BaseIndexer` |   |
| `BaseKVIndexer` |   |
| `BaseNumericEncoder` | `jina.hub.encoders.nlp.TransformerTFEncoder` |
| `BaseNumericEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `BaseNumpyIndexer` | `jina.hub.indexers.vector.MilvusIndexer` |
| `BaseOnnxEncoder` |   |
| `BasePaddleEncoder` |   |
| `BaseRanker` |   |
| `BaseSegmenter` | `jina.hub.crafters.audio.AudioNormalizer` |
| `BaseTFEncoder` |   |
| `BaseTextEncoder` | `jina.hub.encoders.nlp.TransformerTFEncoder` |
| `BaseTorchEncoder` |   |
| `BaseVectorIndexer` |   |
| `BaseVideoEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `BiMatchRanker` | `jina.hub.rankers.TfIdfRanker` |
| `BigTransferEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `BinaryPbIndexer` |   |
| `CenterImageCropper` | `jina.hub.crafters.audio.AudioNormalizer` |
| `ChromaPitchEncoder` | `jina.hub.encoders.audio.MFCCTimbreEncoder` |
| `Chunk2DocRanker` |   |
| `CompressionVaeEncoder` |   |
| `CustomImageTorchEncoder` | `jina.hub.encoders.nlp.FarmTextEncoder` |
| `CustomKerasImageEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `DeepSegmenter` | `jina.hub.crafters.image.RandomImageCropper` |
| `FaissDevice` |   |
| `FaissIndexer` |   |
| `FarmTextEncoder` | `jina.hub.encoders.nlp.FarmTextEncoder` |
| `FastICAEncoder` | `jina.hub.encoders.numeric.FeatureAgglomerationEncoder` |
| `FeatureAgglomerationEncoder` | `jina.hub.encoders.numeric.FeatureAgglomerationEncoder` |
| `FiveImageCropper` | `jina.hub.crafters.image.RandomImageCropper` |
| `FlairTextEncoder` | `jina.hub.encoders.nlp.FarmTextEncoder` |
| `ImageCropper` | `jina.hub.crafters.audio.AudioNormalizer` |
| `ImageFlipper` | `jina.hub.crafters.audio.AudioNormalizer` |
| `ImageKerasEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `ImageNormalizer` | `jina.hub.crafters.audio.AudioNormalizer` |
| `ImageOnnxEncoder` | `jina.hub.encoders.image.ImageOnnxEncoder` |
| `ImagePaddlehubEncoder` | `jina.hub.encoders.nlp.TextPaddlehubEncoder` |
| `ImageReader` | `jina.hub.crafters.audio.AudioNormalizer` |
| `ImageResizer` | `jina.hub.crafters.audio.AudioNormalizer` |
| `ImageTorchEncoder` | `jina.hub.encoders.nlp.FarmTextEncoder` |
| `IncrementalPCAEncoder` | `jina.hub.encoders.numeric.FeatureAgglomerationEncoder` |
| `JiebaSegmenter` | `jina.hub.crafters.image.RandomImageCropper` |
| `LaserEncoder` | `jina.hub.encoders.nlp.FarmTextEncoder` |
| `LevelDBIndexer` | `jina.hub.indexers.keyvalue.MongoDBIndexer` |
| `LevenshteinRanker` | `jina.hub.rankers.LevenshteinRanker` |
| `MFCCTimbreEncoder` | `jina.hub.encoders.audio.MFCCTimbreEncoder` |
| `Match2DocRanker` |   |
| `MaxRanker` | `jina.hub.rankers.TfIdfRanker` |
| `MilvusIndexer` | `jina.hub.indexers.vector.MilvusIndexer` |
| `MinRanker` | `jina.hub.rankers.TfIdfRanker` |
| `MongoDBIndexer` | `jina.hub.indexers.keyvalue.MongoDBIndexer` |
| `NGTIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `NmsLibIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `NumpyIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `OneHotTextEncoder` | `jina.hub.encoders.nlp.OneHotTextEncoder` |
| `OnnxDevice` |   |
| `PDFExtractorSegmenter` | `jina.hub.crafters.image.RandomImageCropper` |
| `PaddleDevice` |   |
| `RandomGaussianEncoder` | `jina.hub.encoders.numeric.FeatureAgglomerationEncoder` |
| `RandomImageCropper` | `jina.hub.crafters.image.RandomImageCropper` |
| `RandomSparseEncoder` | `jina.hub.encoders.numeric.FeatureAgglomerationEncoder` |
| `RedisDBIndexer` | `jina.hub.indexers.keyvalue.MongoDBIndexer` |
| `ScannIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `Sentencizer` | `jina.hub.crafters.image.RandomImageCropper` |
| `SlidingWindowAudioSlicer` | `jina.hub.crafters.image.RandomImageCropper` |
| `SlidingWindowImageCropper` | `jina.hub.crafters.image.RandomImageCropper` |
| `SlidingWindowSegmenter` | `jina.hub.crafters.image.RandomImageCropper` |
| `SptagIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `TFDevice` |   |
| `TSNEEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `TextPaddlehubEncoder` | `jina.hub.encoders.nlp.TextPaddlehubEncoder` |
| `TfIdfRanker` | `jina.hub.rankers.TfIdfRanker` |
| `TikaExtractor` | `jina.hub.crafters.audio.AudioNormalizer` |
| `TorchDevice` |   |
| `TorchObjectDetectionSegmenter` |   |
| `TransformEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `TransformerTFEncoder` |   |
| `TransformerTorchEncoder` |   |
| `UniversalSentenceEncoder` | `jina.hub.encoders.numeric.CompressionVaeEncoder` |
| `VideoPaddleEncoder` | `jina.hub.encoders.nlp.TextPaddlehubEncoder` |
| `VideoTorchEncoder` |   |
| `Wav2VecSpeechEncoder` |   |
| `ZarrIndexer` | `jina.hub.indexers.vector.ZarrIndexer` |