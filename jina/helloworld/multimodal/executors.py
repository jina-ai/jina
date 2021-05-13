import os
from collections import defaultdict
from typing import Dict, Optional, Tuple

import numpy as np

from jina import Executor, DocumentArray, requests, Document, Flow
from helper import _norm, _ext_A, _ext_B, _cosine


class Segmenter(Executor):
    @requests(on=['/index', '/search'])
    def segment(self, docs: DocumentArray, **kwargs):
        """
        Read the data and add tags.

        :param docs: received documents.
        :param ..
        """
        for doc in docs:
            text = doc.tags['caption']
            uri = f'{os.environ["HW_WORKDIR"]}/people-img/{doc.tags["image"]}'
            chunk_text = Document(text=text, mime_type='text/plain')
            chunk_uri = Document(uri=uri, mime_type='image/jpeg')
            doc.chunks.extend([chunk_text, chunk_uri])


class ModalityFilter(Executor):
    def __init__(self, mime_type_to_keep: str, **kwargs):
        super().__init__(**kwargs)
        self.mime_type = mime_type_to_keep

    @requests(on=['/index', '/search'])
    def filter(self, docs: DocumentArray, **kwargs):
        for chunks in docs.traverse(traversal_paths=['c']):
            chunks_to_be_filtered = []
            for idx, chunk in enumerate(chunks):
                if chunk.mime_type != self.mime_type:
                    chunks_to_be_filtered.append(idx)
            for idx in reversed(chunks_to_be_filtered):
                del chunks[idx]


class TextEncoder(Executor):
    def __init__(
        self,
        pretrained_model_name_or_path: str = 'sentence-transformers/distilbert-base-nli-stsb-mean-tokens',
        base_tokenizer_model: Optional[str] = None,
        pooling_strategy: str = 'mean',
        layer_index: int = -1,
        max_length: Optional[int] = None,
        acceleration: Optional[str] = None,
        embedding_fn_name: str = '__call__',
        max_retries: int = 20,
        *args,
        **kwargs,
    ):
        import torch
        from transformers import AutoModel, AutoTokenizer

        super().__init__(*args, **kwargs)
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.base_tokenizer_model = (
            base_tokenizer_model or pretrained_model_name_or_path
        )
        self.pooling_strategy = pooling_strategy
        self.layer_index = layer_index
        self.max_length = max_length
        self.acceleration = acceleration
        self.embedding_fn_name = embedding_fn_name
        self.max_retries = max_retries

        self.tokenizer = AutoTokenizer.from_pretrained(self.base_tokenizer_model)

        self.model = AutoModel.from_pretrained(
            self.pretrained_model_name_or_path, output_hidden_states=True
        )
        self.device = torch.device('cpu')

        if self.acceleration == 'quant':
            self.model = torch.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8
            )

    def amp_accelerate(self):
        """Check acceleration method """
        import torch
        from contextlib import nullcontext

        if self.acceleration == 'amp':
            return torch.cuda.amp.autocast()
        else:
            return nullcontext()

    def _compute_embedding(self, hidden_states: 'torch.Tensor', input_tokens: Dict):
        import torch

        n_layers = len(hidden_states)
        if self.layer_index not in list(range(-n_layers, n_layers)):
            self.logger.error(
                f'Invalid value {self.layer_index} for `layer_index`,'
                f' for the model {self.pretrained_model_name_or_path}'
                f' valid values are integers from {-n_layers} to {n_layers - 1}.'
            )
            raise ValueError

        if self.pooling_strategy == 'cls' and not self.tokenizer.cls_token:
            self.logger.error(
                f'You have set pooling_strategy to "cls", but the tokenizer'
                f' for the model {self.pretrained_model_name_or_path}'
                f' does not have a cls token set.'
            )
            raise ValueError

        fill_vals = {'cls': 0.0, 'mean': 0.0, 'max': -np.inf, 'min': np.inf}
        fill_val = torch.tensor(fill_vals[self.pooling_strategy], device=self.device)

        layer = hidden_states[self.layer_index]
        attn_mask = input_tokens['attention_mask'].unsqueeze(-1).expand_as(layer)
        layer = torch.where(attn_mask.bool(), layer, fill_val)

        if self.pooling_strategy == 'cls':
            CLS = self.tokenizer.cls_token_id
            ind = torch.nonzero(input_tokens['input_ids'] == CLS)[:, 1]
            ind = ind.unsqueeze(-1).unsqueeze(-1).expand(-1, -1, layer.shape[2])
            embeddings = torch.gather(layer, 1, ind).squeeze(dim=1)
        elif self.pooling_strategy == 'mean':
            embeddings = layer.sum(dim=1) / attn_mask.sum(dim=1)
        elif self.pooling_strategy == 'max':
            embeddings = layer.max(dim=1).values
        elif self.pooling_strategy == 'min':
            embeddings = layer.min(dim=1).values

        return embeddings.cpu().numpy()

    @requests(on=['/index', '/search'])
    def encode(self, docs: DocumentArray, **kwargs):
        """
        Read the data and add tags.

        :param docs: received documents.
        :return: crafted data
        """
        import torch

        for doc in docs.traverse_flatten(['c']):
            with torch.no_grad():
                if not self.tokenizer.pad_token:
                    self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                    self.model.resize_token_embeddings(len(self.tokenizer.vocab))

                input_tokens = self.tokenizer(
                    list(doc.content),
                    max_length=self.max_length,
                    padding='longest',
                    truncation=True,
                    return_tensors='pt',
                )
                input_tokens = {k: v.to(self.device) for k, v in input_tokens.items()}

                with self.amp_accelerate():
                    outputs = getattr(self.model, self.embedding_fn_name)(
                        **input_tokens
                    )
                    if isinstance(outputs, torch.Tensor):
                        return outputs.cpu().numpy()
                    hidden_states = outputs.hidden_states
                doc.embedding = self._compute_embedding(hidden_states, input_tokens)


class ImageCrafter(Executor):
    @requests(on=['/index', '/search'])
    def craft(self, docs: DocumentArray, **kwargs):
        for doc in docs.traverse_flatten(['c']):
            doc.convert_image_uri_to_blob()


class ImageEncoder(Executor):
    def __init__(
        self,
        model_name: str = 'mobilenet_v2',
        pool_strategy: str = 'mean',
        channel_axis: int = 1,
        *args,
        **kwargs,
    ):
        import torchvision.models as models

        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis
        # axis 0 is the batch
        self._default_channel_axis = 1
        self.model_name = model_name
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError(f'unknown pool_strategy: {self.pool_strategy}')
        self.pool_strategy = pool_strategy

        if self.pool_strategy is not None:
            self.pool_fn = getattr(np, self.pool_strategy)
        model = getattr(models, self.model_name)(pretrained=True)
        self.model = model.features.eval()

    def _get_features(self, content):
        return self.model(content)

    def _get_pooling(self, feature_map: 'np.ndarray') -> 'np.ndarray':
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return self.pool_fn(feature_map, axis=(2, 3))

    @requests(on=['/index', '/search'])
    def encode(self, docs: DocumentArray, **kwargs):
        import torch

        for doc in docs.traverse_flatten(traversal_paths=['c']):
            if self.channel_axis != self._default_channel_axis:
                content = np.moveaxis(
                    doc.content, self.channel_axis, self._default_channel_axis
                )
            else:
                content = doc.content

            _input = torch.from_numpy(content.astype('float32'))
            _feature = self._get_features(_input).detach()
            _feature = _feature.numpy()
            doc.embedding = self._get_pooling(_feature)


class DocVectorIndexer(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        a = np.stack(docs.get_attributes('embedding'))
        b = np.stack(self._docs.get_attributes('embedding'))
        q_emb = _ext_A(_norm(a))
        d_emb = _ext_B(_norm(b))
        dists = _cosine(q_emb, d_emb)
        idx, dist = self._get_sorted_top_k(dists, int(parameters['top_k']))
        for _q, _ids, _dists in zip(docs, idx, dist):
            for _id, _dist in zip(_ids, _dists):
                d = Document(self._docs[int(_id)], copy=True)
                d.score.value = 1 - _dist
                _q.matches.append(d)

    @staticmethod
    def _get_sorted_top_k(
        dist: 'np.array', top_k: int
    ) -> Tuple['np.ndarray', 'np.ndarray']:
        if top_k >= dist.shape[1]:
            idx = dist.argsort(axis=1)[:, :top_k]
            dist = np.take_along_axis(dist, idx, axis=1)
        else:
            idx_ps = dist.argpartition(kth=top_k, axis=1)[:, :top_k]
            dist = np.take_along_axis(dist, idx_ps, axis=1)
            idx_fs = dist.argsort(axis=1)
            idx = np.take_along_axis(idx_ps, idx_fs, axis=1)
            dist = np.take_along_axis(dist, idx_fs, axis=1)

        return idx, dist


class KeyValueIndexer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.map = {}

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            self.map[doc.id] = doc

    @requests(on='/search')
    def query(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            for match in doc.matches:
                extracted_doc = self.map[doc.id]
                match.MergeFrom(extracted_doc)


class WeightedRanker(Executor):

    COL_PARENT_ID = 'match_parent_id'
    COL_DOC_CHUNK_ID = 'match_doc_chunk_id'
    COL_QUERY_CHUNK_ID = 'match_query_chunk_id'
    COL_SCORE = 'score'

    @requests(on='/search')
    def rank(self, docs: 'DocumentArray', *args, **kwargs) -> None:
        """
        :param docs: the doc which gets bubbled up matches
        :param args: not used (kept to maintain interface)
        :param kwargs: not used (kept to maintain interface)
        """
        for doc in docs:
            chunks = doc.chunks
            match_idx = []  # type: List[Tuple[str, str, str, float]]

            parent_id_chunk_id_map = defaultdict(list)
            matches_by_id = defaultdict(Document)
            for chunk in chunks:

                for match in chunk.matches:
                    match_info = self._extract_query_match_info(
                        match=match, query=chunk
                    )
                    match_idx.append(match_info)

                    parent_id_chunk_id_map[match.parent_id].append(match.id)
                    matches_by_id[match.id] = match

            if match_idx:
                match_idx = np.array(
                    match_idx,
                    dtype=[
                        (self.COL_PARENT_ID, 'U64'),
                        (self.COL_DOC_CHUNK_ID, 'U64'),
                        (self.COL_QUERY_CHUNK_ID, 'U64'),
                        (self.COL_SCORE, np.float64),
                    ],
                )

                docs_scores = self._score(match_idx)

                self._insert_query_matches(
                    query=doc,
                    parent_id_chunk_id_map=parent_id_chunk_id_map,
                    chunk_matches_by_id=matches_by_id,
                    docs_scores=docs_scores,
                )

    @requests(on='/search')
    def score(self, docs: DocumentArray, **kwargs):
        pass
