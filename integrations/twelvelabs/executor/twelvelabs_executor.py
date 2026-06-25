"""A Jina-serve Executor wrapping the TwelveLabs video-understanding API.

It exposes two endpoints:

- ``/embed``   -- Marengo multimodal embeddings (512-dim) for text queries.
- ``/analyze`` -- Pegasus video understanding (text generated from a video).

The ``twelvelabs`` SDK is imported lazily so that this module can be inspected
and the schemas validated without the optional dependency installed.
"""

import os
from typing import Optional

from docarray import BaseDoc, DocList
from docarray.typing import NdArray

from jina import Executor, requests

# Marengo embeddings are 512-dimensional.
MARENGO_EMBEDDING_DIM = 512


class TextDoc(BaseDoc):
    """Input document carrying the text to embed."""

    text: str = ''


class EmbeddingDoc(BaseDoc):
    """Output document carrying a Marengo text embedding."""

    text: str = ''
    embedding: Optional[NdArray[MARENGO_EMBEDDING_DIM]] = None


class VideoPromptDoc(BaseDoc):
    """Input document for Pegasus video analysis."""

    #: A publicly reachable video URL, or a TwelveLabs asset id (see ``video_id``).
    url: str = ''
    #: Alternatively, an already-indexed TwelveLabs ``video_id``.
    video_id: str = ''
    #: The instruction passed to Pegasus, e.g. ``'Summarize this video.'``.
    prompt: str = ''


class AnalysisDoc(BaseDoc):
    """Output document carrying Pegasus-generated text."""

    prompt: str = ''
    text: str = ''


class TwelveLabsExecutor(Executor):
    """Serve TwelveLabs Marengo embeddings and Pegasus video analysis as a Jina Executor.

    Grab a free API key at https://twelvelabs.io (generous free tier) and either
    pass it via ``api_key`` or set the ``TWELVELABS_API_KEY`` environment variable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        embed_model_name: str = 'marengo3.0',
        analyze_model_name: str = 'pegasus1.5',
        max_tokens: int = 2048,
        **kwargs,
    ):
        """Initialize the Executor.

        :param api_key: TwelveLabs API key. Falls back to the ``TWELVELABS_API_KEY``
            environment variable when not provided.
        :param embed_model_name: Marengo model used for ``/embed``.
        :param analyze_model_name: Pegasus model used for ``/analyze``.
        :param max_tokens: Maximum number of tokens Pegasus may generate.
        :param kwargs: Additional keyword arguments forwarded to ``Executor``.
        """
        super().__init__(**kwargs)
        self._api_key = api_key or os.environ.get('TWELVELABS_API_KEY')
        self.embed_model_name = embed_model_name
        self.analyze_model_name = analyze_model_name
        self.max_tokens = max_tokens
        self._client = None

    @property
    def client(self):
        """Lazily build and cache the TwelveLabs client.

        :return: An authenticated ``twelvelabs.TwelveLabs`` client.
        """
        if self._client is None:
            if not self._api_key:
                raise ValueError(
                    'No TwelveLabs API key found. Pass `api_key` or set the '
                    '`TWELVELABS_API_KEY` environment variable.'
                )
            from twelvelabs import TwelveLabs

            self._client = TwelveLabs(api_key=self._api_key)
        return self._client

    @requests(on='/embed')
    def embed(self, docs: DocList[TextDoc], **kwargs) -> DocList[EmbeddingDoc]:
        """Embed each document's text with Marengo into a 512-dim vector.

        :param docs: Documents whose ``text`` field is embedded.
        :param kwargs: Unused, present for endpoint signature compatibility.
        :return: Documents carrying the original text and its embedding.
        """
        out = DocList[EmbeddingDoc]()
        for doc in docs:
            result = self.client.embed.create(
                model_name=self.embed_model_name, text=doc.text
            )
            vector = result.text_embedding.segments[0].float_
            out.append(EmbeddingDoc(text=doc.text, embedding=vector))
        return out

    @requests(on='/analyze')
    def analyze(self, docs: DocList[VideoPromptDoc], **kwargs) -> DocList[AnalysisDoc]:
        """Analyze each video with Pegasus and return the generated text.

        Provide either a public ``url`` or an indexed ``video_id`` per document.

        :param docs: Documents describing the video and the prompt.
        :param kwargs: Unused, present for endpoint signature compatibility.
        :return: Documents carrying the prompt and Pegasus' generated text.
        """
        from twelvelabs.types.video_context import VideoContext_Url

        out = DocList[AnalysisDoc]()
        for doc in docs:
            params = dict(
                model_name=self.analyze_model_name,
                prompt=doc.prompt,
                max_tokens=self.max_tokens,
            )
            if doc.video_id:
                params['video_id'] = doc.video_id
            else:
                params['video'] = VideoContext_Url(url=doc.url)
            result = self.client.analyze(**params)
            out.append(AnalysisDoc(prompt=doc.prompt, text=result.data))
        return out
