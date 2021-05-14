import os
import pickle
from collections import defaultdict, namedtuple
from typing import Dict, Optional, Tuple, List, Union, Iterable

import numpy as np

from jina import Executor, DocumentArray, requests, Document
from jina.types.score import NamedScore
from jina.helloworld.multimodal.helper import (
    _norm,
    _ext_A,
    _ext_B,
    _cosine,
    _load_image,
    _move_channel_axis,
    _resize_short,
    _crop_image,
)


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

    def _compute_embedding(self, hidden_states, input_tokens):
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

        chunks = docs.traverse_flatten(['c'])
        texts = chunks.get_attributes('text')

        with torch.no_grad():
            if not self.tokenizer.pad_token:
                self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                self.model.resize_token_embeddings(len(self.tokenizer.vocab))

            input_tokens = self.tokenizer(
                texts,
                max_length=self.max_length,
                padding='longest',
                truncation=True,
                return_tensors='pt',
            )
            input_tokens = {k: v.to(self.device) for k, v in input_tokens.items()}

            with self.amp_accelerate():
                outputs = getattr(self.model, self.embedding_fn_name)(**input_tokens)
                if isinstance(outputs, torch.Tensor):
                    return outputs.cpu().numpy()
                hidden_states = outputs.hidden_states
                embeddings = self._compute_embedding(hidden_states, input_tokens)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding


class ImageCrafter(Executor):
    def __init__(
        self,
        target_size: Union[Iterable[int], int] = 224,
        img_mean: Tuple[float] = (0, 0, 0),
        img_std: Tuple[float] = (1, 1, 1),
        resize_dim: int = 256,
        channel_axis: int = -1,
        target_channel_axis: int = -1,
        *args,
        **kwargs,
    ):
        """Set Constructor."""
        super().__init__(*args, **kwargs)
        if isinstance(target_size, int):
            self.target_size = target_size
        elif isinstance(target_size, Iterable):
            self.target_size = tuple(target_size)
        else:
            raise ValueError(
                f'target_size {target_size} should be an integer or tuple/list of 2 integers'
            )
        self.resize_dim = resize_dim
        self.img_mean = np.array(img_mean).reshape((1, 1, 3))
        self.img_std = np.array(img_std).reshape((1, 1, 3))
        self.channel_axis = channel_axis
        self.target_channel_axis = target_channel_axis

    @requests(on='/index')
    def craft_index(self, docs: DocumentArray, **kwargs):
        for doc in docs.traverse_flatten(['c']):
            doc.convert_image_uri_to_blob()
            raw_img = _load_image(doc.blob, self.channel_axis)
            _img = self._normalize(raw_img)
            # move the channel_axis to target_channel_axis to better fit different models
            img = _move_channel_axis(_img, -1, self.target_channel_axis)
            doc.blob = img

    @requests(on='/search')
    def craft_search(self, docs: DocumentArray, **kwargs):
        for doc in docs.traverse_flatten(['c']):
            doc.convert_image_datauri_to_blob()
            raw_img = _load_image(doc.blob, self.channel_axis)
            _img = self._normalize(raw_img)
            # move the channel_axis to target_channel_axis to better fit different models
            img = _move_channel_axis(_img, -1, self.target_channel_axis)
            doc.blob = img

    def _normalize(self, img):
        img = _resize_short(img, target_size=self.resize_dim)
        img, _, _ = _crop_image(img, target_size=self.target_size, how='center')
        img = np.array(img).astype('float32') / 255
        img -= self.img_mean
        img /= self.img_std
        return img


class ImageEncoder(Executor):
    def __init__(
        self,
        model_name: str = 'mobilenet_v2',
        pool_strategy: str = 'mean',
        channel_axis: int = -1,
        *args,
        **kwargs,
    ):
        import torch
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
        self.model.to(torch.device('cpu'))

    def _get_features(self, content):
        content = content.permute(0, 3, 1, 2)
        return self.model(content)

    def _get_pooling(self, feature_map: 'np.ndarray') -> 'np.ndarray':
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return self.pool_fn(feature_map, axis=(2, 3))

    @requests(on=['/index', '/search'])
    def encode(self, docs: DocumentArray, **kwargs):
        import torch

        chunks = docs.traverse_flatten(traversal_paths=['c'])
        content = np.stack(chunks.get_attributes('blob'))
        _input = torch.from_numpy(content.astype('float32'))
        _features = self._get_features(_input).detach()
        _features = _features.numpy()
        _features = self._get_pooling(_features)
        for chunk, feature in zip(chunks, _features):
            chunk.embedding = feature


class DocVectorIndexer(Executor):
    def __init__(self, index_file_name: str, **kwargs):
        super().__init__(**kwargs)
        self.index_file_name = index_file_name
        if os.path.exists(self.save_path):
            self._docs = DocumentArray.load(self.save_path)
        else:
            self._docs = DocumentArray()

    @property
    def save_path(self):
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        return os.path.join(self.workspace, self.index_file_name)

    def close(self):
        self._docs.save(self.save_path)

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        self._docs.extend(docs.traverse_flatten(['c']))

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        chunks = docs.traverse_flatten(['c'])
        a = np.stack(chunks.get_attributes('embedding'))
        b = np.stack(self._docs.get_attributes('embedding'))
        q_emb = _ext_A(_norm(a))
        d_emb = _ext_B(_norm(b))
        dists = _cosine(q_emb, d_emb)
        idx, dist = self._get_sorted_top_k(dists, int(parameters['top_k']))
        for _q, _ids, _dists in zip(chunks, idx, dist):
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
        if os.path.exists(self.save_path):
            self._docs = DocumentArray.load(self.save_path)
            with open(self.save_map_path, 'rb') as f:
                self.map = pickle.load(f)
        else:
            self._docs = DocumentArray()

    @property
    def save_path(self):
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        return os.path.join(self.workspace, 'kv.json')

    @property
    def save_map_path(self):
        return os.path.join(self.workspace, 'map.pickle')

    def close(self):
        self._docs.save(self.save_path)
        with open(self.save_map_path, 'wb') as f:
            pickle.dump(self.map, f)

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            inner_id = len(self._docs)
            self._docs.append(doc)
            self.map[doc.id] = inner_id

    @requests(on='/search')
    def query(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            for match in doc.matches:
                inner_id = self.map[match.id]
                extracted_doc = self._docs[inner_id]
                match.MergeFrom(extracted_doc)


class WeightedRanker(Executor):
    COL_PARENT_ID = 'match_parent_id'
    COL_DOC_CHUNK_ID = 'match_doc_chunk_id'
    COL_QUERY_CHUNK_ID = 'match_query_chunk_id'
    COL_SCORE = 'score'
    QueryMatchInfo = namedtuple(
        'QueryMatchInfo', 'match_parent_id match_id query_id score'
    )

    def _score(self, match_idx: 'np.ndarray', query_chunk_meta: Dict) -> 'np.ndarray':
        _groups = self._group_by(match_idx, self.COL_PARENT_ID)
        n_groups = len(_groups)
        res = np.empty(
            (n_groups,),
            dtype=[
                (self.COL_PARENT_ID, 'U64'),
                (self.COL_SCORE, np.float64),
            ],
        )

        for i, _g in enumerate(_groups):
            res[i] = (
                _g[self.COL_PARENT_ID][0],
                self.score(_g, query_chunk_meta),
            )

        self._sort_doc_by_score(res)
        return res

    def _sort_doc_by_score(self, r):
        """
        Sort a numpy array  of dtype (``doc_id``, ``score``) by the ``score``.
        :param r: Numpy array of Tuples with document id and score
        :type r: np.ndarray[Tuple[np.str_, np.float64]]
        """
        r[::-1].sort(order=self.COL_SCORE)

    def _group_by(self, match_idx, col_name):
        """
        Create an list of numpy arrays with the same ``col_name`` in each position of the list
        :param match_idx: Numpy array of Tuples with document id and score
        :param col_name:  Column name in the structured numpy array of Tuples
        :return: List of numpy arrays with the same ``doc_id`` in each position of the list
        :rtype: np.ndarray.
        """
        _sorted_m = np.sort(match_idx, order=col_name)
        list_numpy_arrays = []
        prev_val = _sorted_m[col_name][0]
        prev_index = 0
        for i, current_val in enumerate(_sorted_m[col_name]):
            if current_val != prev_val:
                list_numpy_arrays.append(_sorted_m[prev_index:i])
                prev_index = i
                prev_val = current_val
        list_numpy_arrays.append(_sorted_m[prev_index:])
        return list_numpy_arrays

    def _insert_query_matches(
        self,
        query: Document,
        docs_scores: 'np.ndarray',
    ):
        """
        :param query: the query Document where the resulting matches will be inserted
        :param docs_scores: An `np.ndarray` resulting from the ranker executor with the `scores` of the new matches
        """
        op_name = self.score.__class__.__name__
        for doc_id, score in docs_scores:
            m = Document(id=doc_id)
            m.score = NamedScore(op_name=op_name, value=score)
            query.matches.append(m)

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
            query_meta = {}  # type: Dict[str, Dict]

            parent_id_chunk_id_map = defaultdict(list)
            matches_by_id = defaultdict(Document)
            for chunk in chunks:
                query_meta[chunk.id] = {}
                query_meta[chunk.id]['weight'] = chunk.weight
                for match in chunk.matches:
                    match_info = self.QueryMatchInfo(
                        match_parent_id=match.parent_id,
                        match_id=match.id,
                        query_id=chunk.id,
                        score=match.score.value,
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

                docs_scores = self._score(match_idx, query_chunk_meta=query_meta)
                self._insert_query_matches(
                    query=doc,
                    docs_scores=docs_scores,
                )

    def score(self, match_idx, query_chunk_meta):
        scores = match_idx[[self.COL_QUERY_CHUNK_ID, self.COL_SCORE]]
        weight_score = 0.0
        for k, v in scores:
            vv = 1 / (1 + v)
            weight_score += query_chunk_meta[k]['weight'] * vv
        return weight_score
