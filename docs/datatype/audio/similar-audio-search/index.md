# Search Similar Audios

Searching for similar audios has a wide range of application including finding similar songs, replacing curse words and detecting the speakers. In this tutorial, we will build an example of searching similar audios using the [AudioSet](https://research.google.com/audioset/) dataset and the [VGGish](https://github.com/tensorflow/models/tree/master/research/audioset/vggish) model.

## Build the Flow

```{figure} similar-audio-search-flow.svg
:align: center
```

### Segment the Audio Clips

The AudioSet dataset contains millions of annotated audios extracted from YouTube videos. Each sound clip is 10-second long and labeled to 632 audio event classes. 
One major challenges is that some sound clips contains other events. This makes it difficult and nosiy to express the whole clip with a single vector. For example, the audio clip below is labled as `applause` but contains a long part of music. To overcome this issue, we use the [recursive structure](https://docs.jina.ai/fundamentals/document/document-api/#recursive-nested-document) of Jina Document and split the clips into smaller chunks. Each chunk contains a smaller clip of 4-second. 

<audio controls>
  <source src="../../_static/similar-audio-search-match-UE3XnVFodMI_230000_applause.mp3" type="audio/wav">
Your browser does not support the audio element.
</audio>


```{admonition} Tips
:class: info

The AudioSet dataset doesn't contain the original sound clip. You can use `youtube-dl` to download the audio data from the corresponding YouTube videos:

:::text
youtube-dl --postprocessor-args '-ss 8.953 -to 18.953' -x --audio-format mp3 -o 'data/OXJ9Ln2sXJ8_30000.%(ext)s' https://www.youtube.com/watch\?v\=OXJ9Ln2sXJ8_30000
:::
```

To segment the audio clips into 4-second chunks, we define `AudioSegmenter` which loads the audio files into `ndarray` and split the array based on the `window_size`. The extracted audio data is stored in the `blob` attribute of the chunks. The file path of the audio files is defined in the `uri` attribute. We also set `stride` for hopping the sliding window. Using `stride=2` and `window_size=4`, we genereate 4 chunks for each 10-second audio, in which each chunk has 2 seconds overlapped with the previous one.

```python
import librosa as lr

class AudioSegmenter(Executor):
    def __init__(self, window_size: float = 4, stride: float = 2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_size = window_size  # seconds
        self.stride = stride

    @requests(on=['/index', '/search'])
    def segment(self, docs: DocumentArray, **kwargs):
        for idx, doc in enumerate(docs):
            try:
                doc.blob, sample_rate = lr.load(doc.uri, sr=16000)
            except RuntimeError as e:
                print(f'failed to load {doc.uri}, {e}')
                continue
            doc.tags['sample_rate'] = sample_rate
            chunk_size = int(self.window_size * sample_rate)
            stride_size = int(self.stride * sample_rate)
            num_chunks = max(1, int((doc.blob.shape[0] - chunk_size) / stride_size))
            for chunk_id in range(num_chunks):
                beg = chunk_id * stride_size
                end = beg + chunk_size
                if beg > doc.blob.shape[0]:
                    break
                c = Document(
                    blob=doc.blob[beg:end],
                    offset=idx,
                    location=[beg, end],
                    tags=doc.tags,
                    uri=doc.uri
                )
                doc.chunks.append(c)
```

```{admonition} Note
:class: important

`sample_rate` is required for generating log mel spectrogram features and therefore we store this information at `tags['sample_rate']`.

```

```{admonition} Tips
:class: info

The length of audios might not be exactly 10 seconds and therefore the number of extract chunks might vary from audio to audio.

```

### Encode the Audios

To encode the sound clips into vectors, we choose VGGish model from Google Research. By default, the VGGish model needs the audios to be sampled at 16kHz and converted to examples of log mel spectrogram. The returning embeddings for each sound clip is a matrix of the size `K x 128`, where `K` is the number of examples in log mel spectrogram and roughly correpsond to the length of audio in seconds. Therefore, each 4-second audio clip in the chunks is represented by 4 128-dimensional vectors.

Since the sequence of the sounds matters, we further concatenate the 4 vectors for each audio clip and consider the resulted 512-dimensional vector as the final representation. After encoding indexing and querying audios are encoded into 1280-dimensional vectors, we can find the similar audios to the querying ones by looking for nearest neighbors in the vector space.

[VGGishAudioEncoder](https://hub.jina.ai/executor/jypyr28o) is available at Jina Hub. It accepts the audio Documents with waveform data stored in the `blob` attribute as `ndarray`. The `load_input_from` argument is to configurate the input data type, which can be each `uri`, `waveform` or `log_mel`. The `min_duration` defines the number of vectors to concatenate. 

```yaml
  ...
  - name: 'encoder'
    uses: 'jinahub+docker://VGGishAudioEncoder/v0.4'
    uses_with:
      traversal_paths: ['c', ]
      load_input_from: 'waveform'
      min_duration: 4
    volumes:
      - './models:/workspace/models'
  ...
```

```{admonition} Note
:class: important

When choosing `waveform` in VGGishAudioEncoder, we need to provide `sample_rate` at `tags['sample_rate']` for generating log mel spectrogram features.

```
### Storage

We choose the [SimpleIndexer](https://hub.jina.ai/executor/zb38xlt4) from Jina Hub for building a simple index storing both embedding vectors and meta information. During querying, we need to split the querying audios in the same way as indexing and generating chunks. Therefore, we need to set both `traversal_rdarray` and `traversal_ldarray` to `['c',]` to ask the SimpleIndexer to use the embeddings of the chunks for the querying and the indexed Documents correspondingly.

```yaml
  ...
  - name: 'indexer'
    uses: 'jinahub://SimpleIndexer/v0.7'
    uses_with:
      match_args:
        limit: 5
        traversal_rdarray: ['c',]
        traversal_ldarray: ['c',]
  ...
```

### Merge the Matches

Since we use audio chunks to retrieve the matches, we need to merge the retrieved matches into the matches for each query audio. We write `MyRanker` as below to collect the orginal 10-second audio clip for each retrieved 4-second short clips. Each long clip is retrieved for multiple times base on different parts of its short clips. We use the score of the most matched short clip as the score of the long audio. Afterwards, the retrieved long audios are sorted by their scores.

```python
class MyRanker(Executor):
    @requests(on='/search')
    def rank(self, docs: DocumentArray = None, **kwargs):
        for doc in docs.traverse_flat(('r', )):
            parents_scores = defaultdict(list)
            parents_match = defaultdict(list)
            for m in DocumentArray([doc]).traverse_flat(['cm']):
                parents_scores[m.parent_id].append(m.scores['cosine'].value)
                parents_match[m.parent_id].append(m)
            new_matches = []
            for match_parent_id, scores in parents_scores.items():
                score_id = np.argmin(scores)
                score = scores[score_id]
                match = parents_match[match_parent_id][score_id]
                new_match = Document(
                    uri=match.uri,
                    id=match_parent_id,
                    scores={'cosine': score})
                new_matches.append(new_match)
            # Sort the matches
            doc.matches = new_matches
            doc.matches.sort(key=lambda d: d.scores['cosine'].value)
```

## Run the Flow

As we defined the flow in the YAML file, we use the `load_config` function to create the Flow and index the data.

```python
from jina import DocumentArray, Flow
from jina.types.document.generators import from_files

docs = DocumentArray(from_files('toy-data/*.mp3'))

f = Flow.load_config('flow.yml')
with f:
    f.post(on='/index', inputs=docs)
    f.protocol = 'http'
    f.cors = True
    f.block()
```

### Query from Python
With the Flow running as a http service, we can use the Jina swagger UI tool to query. 
Open the browser at `localhost:45678/docs`, send query via the Swagger UI,

```json
{
  "data": [
    {
      "uri": "toy-data/6pO06krKrf8_30000_airplane.mp3"
    }
  ]
}
```

## Show Resutls


<table>
  <tr>
    <th>Query</th>
    <th>Matches</th>
    <th>Score</th>
  </tr>
  <tr>
    <td><audio controls><source src="../../_static/similar-audio-search-query-hhzoH17yf3o_20000_airplane.mp3" type="audio/wav"></audio></td>
    <td><audio controls><source src="../../_static/similar-audio-search-match-6pO06krKrf8_30000_airplane.mp3" type="audio/wav"></audio></td>
    <td>0.000014126301</td>
  </tr>
  <tr>
    <td></td>
    <td><audio controls><source src="../../_static/similar-audio-search-match-UE3XnVFodMI_230000_applause.mp3" type="audio/wav"></audio></td>
    <td>0.00002515316</td>
  </tr>
</table>

## Get the Source Code

The code is available at [example-audio-search](https://github.com/jina-ai/example-audio-search)