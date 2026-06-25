# Serve TwelveLabs video understanding

This tutorial shows how to serve [TwelveLabs](https://twelvelabs.io) video
understanding as a Jina-serve {class}`~jina.Executor`. The Executor wraps two
TwelveLabs models behind standard endpoints:

- `/embed` returns Marengo multimodal embeddings (512-dim) for text queries.
- `/analyze` returns Pegasus-generated text describing a video.

The full, runnable Executor lives in
[`integrations/twelvelabs`](https://github.com/jina-ai/serve/tree/master/integrations/twelvelabs)
in this repository.

## Before you start

Grab a free API key at [twelvelabs.io](https://twelvelabs.io) (there is a
generous free tier), then install the dependencies and set the key:

```bash
pip install jina twelvelabs
export TWELVELABS_API_KEY=<your-key>
```

## Serve the Executor

```python
from docarray import DocList
from jina import Deployment

from executor import EmbeddingDoc, TextDoc, TwelveLabsExecutor

dep = Deployment(uses=TwelveLabsExecutor, port=12345)

with dep:
    docs = dep.post(
        on='/embed',
        inputs=DocList[TextDoc]([TextDoc(text='a red car driving on a highway')]),
        return_type=DocList[EmbeddingDoc],
    )
    print(docs[0].embedding.shape)
```

The embedding is a 512-dimensional vector, ready for indexing or similarity
search alongside Marengo video embeddings.

## Analyze a video

Provide a public video URL (or an indexed TwelveLabs `video_id`) and a prompt:

```python
from docarray import DocList

from executor import AnalysisDoc, VideoPromptDoc

with dep:
    docs = dep.post(
        on='/analyze',
        inputs=DocList[VideoPromptDoc](
            [
                VideoPromptDoc(
                    url='https://example.com/sample.mp4', prompt='Summarize this video.'
                )
            ]
        ),
        return_type=DocList[AnalysisDoc],
    )
    print(docs[0].text)
```

## See also

- [TwelveLabs documentation](https://docs.twelvelabs.io)
- {ref}`Deploy a model<deploy-model>`
