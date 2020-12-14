# List of 100 Executors in Jina

This version of Jina includes 100 Executors.

## Inheritances in a Tree View
- `BaseExecutor`
   - `BaseEncoder`
      - `BaseDevice`
         - `TFDevice`
            - `BaseTFEncoder`
               - `BigTransferEncoder`
               - `CustomKerasImageEncoder`
               - `BaseNumericEncoder`
                  - `CompressionVaeEncoder`
               - `ImageKerasEncoder`
               - `UniversalSentenceEncoder`
            - `TransformerTFEncoder`
         - `TorchDevice`
            - `BaseTorchEncoder`
               - `FarmTextEncoder`
               - `FlairTextEncoder`
               - `ImageTorchEncoder`
               - `LaserEncoder`
               - `CustomImageTorchEncoder`
            - `TransformerTorchEncoder`
         - `PaddleDevice`
            - `BasePaddleEncoder`
               - `ImagePaddlehubEncoder`
               - `VideoPaddleEncoder`
               - `TextPaddlehubEncoder`
         - `OnnxDevice`
            - `BaseOnnxEncoder`
               - `ImageOnnxEncoder`
      - `BaseNumericEncoder`
         - `TransformEncoder`
            - `RandomSparseEncoder`
            - `FeatureAgglomerationEncoder`
            - `IncrementalPCAEncoder`
            - `FastICAEncoder`
            - `RandomGaussianEncoder`
         - `BaseAudioEncoder`
            - `BaseDevice`
               - `TorchDevice`
                  - `BaseTorchEncoder`
                     - `Wav2VecSpeechEncoder`
            - `ChromaPitchEncoder`
            - `MFCCTimbreEncoder`
         - `BaseVideoEncoder`
            - `BaseDevice`
               - `TorchDevice`
                  - `BaseTorchEncoder`
                     - `VideoTorchEncoder`
         - `TSNEEncoder`
      - `BaseTextEncoder`
         - `OneHotTextEncoder`
   - `BaseIndexer`
      - `BaseVectorIndexer`
         - `BaseNumpyIndexer`
            - `SptagIndexer`
            - `ScannIndexer`
            - `NGTIndexer`
            - `NumpyIndexer`
               - `ZarrIndexer`
            - `AnnoyIndexer`
            - `BaseDevice`
               - `FaissDevice`
                  - `FaissIndexer`
            - `NmsLibIndexer`
         - `MilvusIndexer`
      - `BaseKVIndexer`
         - `BinaryPbIndexer`
            - `LevelDBIndexer`
            - `MongoDBIndexer`
            - `RedisDBIndexer`
   - `BaseCrafter`
      - `BaseSegmenter`
         - `SlidingWindowSegmenter`
         - `SlidingWindowAudioSlicer`
         - `SlidingWindowImageCropper`
         - `JiebaSegmenter`
         - `DeepSegmenter`
         - `RandomImageCropper`
         - `BaseDevice`
            - `TorchDevice`
               - `TorchObjectDetectionSegmenter`
         - `AudioSlicer`
         - `Sentencizer`
         - `PDFExtractorSegmenter`
         - `FiveImageCropper`
      - `ImageCropper`
      - `AudioReader`
      - `TikaExtractor`
      - `CenterImageCropper`
      - `ImageNormalizer`
      - `ArrayStringReader`
      - `ImageReader`
      - `ImageFlipper`
      - `ImageResizer`
      - `AudioNormalizer`
      - `ArrayBytesReader`
      - `AudioMonophoner`
   - `BaseRanker`
      - `Match2DocRanker`
         - `LevenshteinRanker`
      - `Chunk2DocRanker`
         - `TfIdfRanker`
         - `MaxRanker`
         - `BM25Ranker`
         - `MinRanker`
         - `BiMatchRanker`

## Modules in a Table View 

| Class | Module |
| --- | --- |
| `AnnoyIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `ArrayBytesReader` | `jina.hub.crafters.audio.AudioMonophoner` |
| `ArrayStringReader` | `jina.hub.crafters.audio.AudioMonophoner` |
| `AudioMonophoner` | `jina.hub.crafters.audio.AudioMonophoner` |
| `AudioNormalizer` | `jina.hub.crafters.audio.AudioMonophoner` |
| `AudioReader` | `jina.hub.crafters.audio.AudioMonophoner` |
| `AudioSlicer` | `jina.hub.crafters.image.FiveImageCropper` |
| `BM25Ranker` | `jina.hub.rankers.BiMatchRanker` |
| `BaseAudioEncoder` | `jina.hub.encoders.numeric.TSNEEncoder` |
| `BaseCrafter` |   |
| `BaseDevice` | `jina.hub.crafters.image.FiveImageCropper` |
| `BaseDevice` | `jina.hub.encoders.audio.MFCCTimbreEncoder` |
| `BaseDevice` | `jina.hub.encoders.nlp.TransformerTFEncoder` |
| `BaseDevice` | `jina.hub.encoders.video.VideoTorchEncoder` |
| `BaseDevice` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `BaseEncoder` |   |
| `BaseExecutor` |   |
| `BaseIndexer` |   |
| `BaseKVIndexer` |   |
| `BaseNumericEncoder` | `jina.hub.encoders.nlp.TransformerTFEncoder` |
| `BaseNumericEncoder` | `jina.hub.encoders.nlp.UniversalSentenceEncoder` |
| `BaseNumpyIndexer` | `jina.hub.indexers.vector.MilvusIndexer` |
| `BaseOnnxEncoder` |   |
| `BasePaddleEncoder` |   |
| `BaseRanker` |   |
| `BaseSegmenter` | `jina.hub.crafters.audio.AudioMonophoner` |
| `BaseTFEncoder` |   |
| `BaseTextEncoder` | `jina.hub.encoders.nlp.TransformerTFEncoder` |
| `BaseTorchEncoder` |   |
| `BaseVectorIndexer` |   |
| `BaseVideoEncoder` | `jina.hub.encoders.numeric.TSNEEncoder` |
| `BiMatchRanker` | `jina.hub.rankers.BiMatchRanker` |
| `BigTransferEncoder` | `jina.hub.encoders.nlp.UniversalSentenceEncoder` |
| `BinaryPbIndexer` |   |
| `CenterImageCropper` | `jina.hub.crafters.audio.AudioMonophoner` |
| `ChromaPitchEncoder` | `jina.hub.encoders.audio.MFCCTimbreEncoder` |
| `Chunk2DocRanker` |   |
| `CompressionVaeEncoder` |   |
| `CustomImageTorchEncoder` | `jina.hub.encoders.image.CustomImageTorchEncoder` |
| `CustomKerasImageEncoder` | `jina.hub.encoders.nlp.UniversalSentenceEncoder` |
| `DeepSegmenter` | `jina.hub.crafters.image.FiveImageCropper` |
| `FaissDevice` |   |
| `FaissIndexer` |   |
| `FarmTextEncoder` | `jina.hub.encoders.image.CustomImageTorchEncoder` |
| `FastICAEncoder` | `jina.hub.encoders.numeric` |
| `FeatureAgglomerationEncoder` | `jina.hub.encoders.numeric` |
| `FiveImageCropper` | `jina.hub.crafters.image.FiveImageCropper` |
| `FlairTextEncoder` | `jina.hub.encoders.image.CustomImageTorchEncoder` |
| `ImageCropper` | `jina.hub.crafters.audio.AudioMonophoner` |
| `ImageFlipper` | `jina.hub.crafters.audio.AudioMonophoner` |
| `ImageKerasEncoder` | `jina.hub.encoders.nlp.UniversalSentenceEncoder` |
| `ImageNormalizer` | `jina.hub.crafters.audio.AudioMonophoner` |
| `ImageOnnxEncoder` | `jina.hub.encoders.image.ImageOnnxEncoder` |
| `ImagePaddlehubEncoder` | `jina.hub.encoders.nlp.TextPaddlehubEncoder` |
| `ImageReader` | `jina.hub.crafters.audio.AudioMonophoner` |
| `ImageResizer` | `jina.hub.crafters.audio.AudioMonophoner` |
| `ImageTorchEncoder` | `jina.hub.encoders.image.CustomImageTorchEncoder` |
| `IncrementalPCAEncoder` | `jina.hub.encoders.numeric` |
| `JiebaSegmenter` | `jina.hub.crafters.image.FiveImageCropper` |
| `LaserEncoder` | `jina.hub.encoders.image.CustomImageTorchEncoder` |
| `LevelDBIndexer` | `jina.hub.indexers.keyvalue.RedisDBIndexer` |
| `LevenshteinRanker` | `jina.hub.rankers.LevenshteinRanker` |
| `MFCCTimbreEncoder` | `jina.hub.encoders.audio.MFCCTimbreEncoder` |
| `Match2DocRanker` |   |
| `MaxRanker` | `jina.hub.rankers.BiMatchRanker` |
| `MilvusIndexer` | `jina.hub.indexers.vector.MilvusIndexer` |
| `MinRanker` | `jina.hub.rankers.BiMatchRanker` |
| `MongoDBIndexer` | `jina.hub.indexers.keyvalue.RedisDBIndexer` |
| `NGTIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `NmsLibIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `NumpyIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `OneHotTextEncoder` | `jina.hub.encoders.nlp.OneHotTextEncoder` |
| `OnnxDevice` |   |
| `PDFExtractorSegmenter` | `jina.hub.crafters.image.FiveImageCropper` |
| `PaddleDevice` |   |
| `RandomGaussianEncoder` | `jina.hub.encoders.numeric` |
| `RandomImageCropper` | `jina.hub.crafters.image.FiveImageCropper` |
| `RandomSparseEncoder` | `jina.hub.encoders.numeric` |
| `RedisDBIndexer` | `jina.hub.indexers.keyvalue.RedisDBIndexer` |
| `ScannIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `Sentencizer` | `jina.hub.crafters.image.FiveImageCropper` |
| `SlidingWindowAudioSlicer` | `jina.hub.crafters.image.FiveImageCropper` |
| `SlidingWindowImageCropper` | `jina.hub.crafters.image.FiveImageCropper` |
| `SlidingWindowSegmenter` | `jina.hub.crafters.image.FiveImageCropper` |
| `SptagIndexer` | `jina.hub.indexers.vector.NmsLibIndexer` |
| `TFDevice` |   |
| `TSNEEncoder` | `jina.hub.encoders.numeric.TSNEEncoder` |
| `TextPaddlehubEncoder` | `jina.hub.encoders.nlp.TextPaddlehubEncoder` |
| `TfIdfRanker` | `jina.hub.rankers.BiMatchRanker` |
| `TikaExtractor` | `jina.hub.crafters.audio.AudioMonophoner` |
| `TorchDevice` |   |
| `TorchObjectDetectionSegmenter` |   |
| `TransformEncoder` | `jina.hub.encoders.numeric.TSNEEncoder` |
| `TransformerTFEncoder` |   |
| `TransformerTorchEncoder` |   |
| `UniversalSentenceEncoder` | `jina.hub.encoders.nlp.UniversalSentenceEncoder` |
| `VideoPaddleEncoder` | `jina.hub.encoders.nlp.TextPaddlehubEncoder` |
| `VideoTorchEncoder` |   |
| `Wav2VecSpeechEncoder` |   |
| `ZarrIndexer` | `jina.hub.indexers.vector.ZarrIndexer` |