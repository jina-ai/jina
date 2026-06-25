# TwelveLabs Executor

Serve [TwelveLabs](https://twelvelabs.io) video understanding as a Jina-serve
Executor. It wraps two TwelveLabs models behind standard Jina endpoints:

- **`/embed`** &mdash; Marengo multimodal embeddings (512-dim) for text queries.
- **`/analyze`** &mdash; Pegasus video understanding (text generated from a video).

This is an opt-in, self-contained example Executor. It does not change any core
Jina-serve behaviour and the `twelvelabs` SDK is only imported when the Executor
actually runs.

## Install

```bash
pip install -r requirements.txt
```

Grab a free API key at <https://twelvelabs.io> (there's a generous free tier),
then either pass it via `api_key` or export it:

```bash
export TWELVELABS_API_KEY=<your-key>
```

## Use in Python

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
    print(docs[0].embedding.shape)  # (512,)
```

Analyze a public video with Pegasus:

```python
from docarray import DocList

from executor import AnalysisDoc, VideoPromptDoc

docs = dep.post(
    on='/analyze',
    inputs=DocList[VideoPromptDoc](
        [
            VideoPromptDoc(
                url='https://example.com/sample.mp4',
                prompt='Summarize this video.',
            )
        ]
    ),
    return_type=DocList[AnalysisDoc],
)
print(docs[0].text)
```

## Use via YAML

```yaml
jtype: TwelveLabsExecutor
py_modules:
  - executor/__init__.py
with:
  embed_model_name: marengo3.0
  analyze_model_name: pegasus1.5
```

## Configuration

| Argument             | Default        | Description                                   |
| -------------------- | -------------- | --------------------------------------------- |
| `api_key`            | env var        | TwelveLabs API key (`TWELVELABS_API_KEY`).    |
| `embed_model_name`   | `marengo3.0`   | Marengo model used by `/embed`.               |
| `analyze_model_name` | `pegasus1.5`   | Pegasus model used by `/analyze`.             |
| `max_tokens`         | `2048`         | Max tokens Pegasus may generate.              |

## Tests

The no-network unit tests run anywhere; the live test runs only when
`TWELVELABS_API_KEY` is set:

```bash
pip install pytest
pytest tests/
```
