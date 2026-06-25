import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docarray import DocList
from executor import (
    AnalysisDoc,
    EmbeddingDoc,
    TextDoc,
    TwelveLabsExecutor,
    VideoPromptDoc,
)

MARENGO_DIM = 512


class _FakeEmbed:
    def create(self, *, model_name, text):
        segment = SimpleNamespace(float_=[0.0] * MARENGO_DIM)
        return SimpleNamespace(text_embedding=SimpleNamespace(segments=[segment]))


class _FakeClient:
    def __init__(self):
        self.embed = _FakeEmbed()

    def analyze(self, **kwargs):
        return SimpleNamespace(data='a generated description')


def test_embed_no_network(monkeypatch):
    """``/embed`` maps text to a 512-dim embedding without hitting the network."""
    exec = TwelveLabsExecutor(api_key='fake')
    monkeypatch.setattr(
        TwelveLabsExecutor, 'client', property(lambda self: _FakeClient())
    )

    docs = DocList[TextDoc]([TextDoc(text='a red car')])
    out = exec.embed(docs)

    assert isinstance(out[0], EmbeddingDoc)
    assert out[0].text == 'a red car'
    assert out[0].embedding.shape == (MARENGO_DIM,)


def test_analyze_no_network(monkeypatch):
    """``/analyze`` returns Pegasus text and wires the video url through."""
    exec = TwelveLabsExecutor(api_key='fake')
    monkeypatch.setattr(
        TwelveLabsExecutor, 'client', property(lambda self: _FakeClient())
    )

    docs = DocList[VideoPromptDoc](
        [VideoPromptDoc(url='https://example.com/v.mp4', prompt='Summarize.')]
    )
    out = exec.analyze(docs)

    assert isinstance(out[0], AnalysisDoc)
    assert out[0].prompt == 'Summarize.'
    assert out[0].text == 'a generated description'


def test_missing_api_key_raises(monkeypatch):
    """Accessing the client without a key gives a clear error."""
    monkeypatch.delenv('TWELVELABS_API_KEY', raising=False)
    exec = TwelveLabsExecutor()
    with pytest.raises(ValueError, match='API key'):
        _ = exec.client


@pytest.mark.skipif(
    not os.environ.get('TWELVELABS_API_KEY'),
    reason='requires TWELVELABS_API_KEY',
)
def test_embed_marengo_live():
    """Live Marengo call returns a real 512-dim embedding."""
    exec = TwelveLabsExecutor()
    out = exec.embed(DocList[TextDoc]([TextDoc(text='a red car driving on a highway')]))
    assert out[0].embedding.shape == (MARENGO_DIM,)
