import os
from typing import Dict, List, Iterable, Union, Tuple

import numpy as np
import torch
import torchvision.models as models
from transformers import AutoModel, AutoTokenizer

from jina import Executor, DocumentArray, requests, Document
from jina.types.arrays.memmap import DocumentArrayMemmap


class Segmenter(Executor):
    @requests
    def segment(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            text = doc.tags['caption']
            uri = f'{os.environ["HW_WORKDIR"]}/people-img/{doc.tags["image"]}'
            chunk_text = Document(text=text, mime_type='text/plain')
            chunk_uri = Document(uri=uri, mime_type='image/jpeg')
            doc.chunks = [chunk_text, chunk_uri]
            doc.uri = uri
            doc.convert_uri_to_datauri()


class TextEncoder(Executor):
    """Transformer executor class"""

    def __init__(
        self,
        pretrained_model_name_or_path: str = 'sentence-transformers/paraphrase-mpnet-base-v2',
        pooling_strategy: str = 'mean',
        layer_index: int = -1,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.pooling_strategy = pooling_strategy
        self.layer_index = layer_index
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.pretrained_model_name_or_path
        )
        self.model = AutoModel.from_pretrained(
            self.pretrained_model_name_or_path, output_hidden_states=True
        )
        self.model.to(torch.device('cpu'))

    def _compute_embedding(self, hidden_states: 'torch.Tensor', input_tokens: Dict):
        fill_vals = {'cls': 0.0, 'mean': 0.0, 'max': -np.inf, 'min': np.inf}
        fill_val = torch.tensor(
            fill_vals[self.pooling_strategy], device=torch.device('cpu')
        )

        layer = hidden_states[self.layer_index]
        attn_mask = input_tokens['attention_mask'].unsqueeze(-1).expand_as(layer)
        layer = torch.where(attn_mask.bool(), layer, fill_val)

        embeddings = layer.sum(dim=1) / attn_mask.sum(dim=1)
        return embeddings.cpu().numpy()

    @requests
    def encode(self, docs: 'DocumentArray', **kwargs):
        with torch.no_grad():
            if not self.tokenizer.pad_token:
                self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                self.model.resize_token_embeddings(len(self.tokenizer.vocab))

            input_tokens = self.tokenizer(
                docs.get_attributes('content'),
                padding='longest',
                truncation=True,
                return_tensors='pt',
            )
            input_tokens = {
                k: v.to(torch.device('cpu')) for k, v in input_tokens.items()
            }

            outputs = self.model(**input_tokens)
            hidden_states = outputs.hidden_states

            embeds = self._compute_embedding(hidden_states, input_tokens)
            docs.embeddings = embeds


class TextCrafter(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests()
    def filter(self, docs: DocumentArray, **kwargs):
        filtered_docs = DocumentArray(
            d for d in docs.traverse_flat(['c']) if d.mime_type == 'text/plain'
        )
        return filtered_docs


class ImageCrafter(Executor):
    def __init__(
        self,
        target_size: Union[Iterable[int], int] = 224,
        img_mean: Tuple[float] = (0, 0, 0),
        img_std: Tuple[float] = (1, 1, 1),
        resize_dim: int = 256,
        channel_axis: int = -1,
        target_channel_axis: int = 0,
        *args,
        **kwargs,
    ):
        """Set Constructor."""
        super().__init__(*args, **kwargs)
        self.target_size = target_size
        self.resize_dim = resize_dim
        self.img_mean = np.array(img_mean).reshape((1, 1, 3))
        self.img_std = np.array(img_std).reshape((1, 1, 3))
        self.channel_axis = channel_axis
        self.target_channel_axis = target_channel_axis

    def craft(self, docs: DocumentArray, fn):
        filtered_docs = DocumentArray(
            d for d in docs.traverse_flat(['c']) if d.mime_type == 'image/jpeg'
        )
        for doc in filtered_docs:
            getattr(doc, fn)()
            raw_img = _load_image(doc.blob, self.channel_axis)
            img = self._normalize(raw_img)
            # move the channel_axis to target_channel_axis to better fit different models
            if self.channel_axis != self.target_channel_axis:
                img = np.moveaxis(img, self.channel_axis, self.target_channel_axis)
            doc.blob = img
        return filtered_docs

    @requests(on='/index')
    def craft_index(self, docs: DocumentArray, **kwargs):
        return self.craft(docs, 'convert_image_uri_to_blob')

    @requests(on='/search')
    def craft_search(self, docs: DocumentArray, **kwargs):
        return self.craft(docs, 'convert_image_datauri_to_blob')

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

        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis
        # axis 0 is the batch
        self._default_channel_axis = 1
        self.model_name = model_name
        self.pool_strategy = pool_strategy
        self.pool_fn = getattr(np, self.pool_strategy)
        model = getattr(models, self.model_name)(pretrained=True)
        self.model = model.features.eval()
        self.model.to(torch.device('cpu'))

    def _get_features(self, content):
        return self.model(content)

    def _get_pooling(self, feature_map: 'np.ndarray') -> 'np.ndarray':
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return self.pool_fn(feature_map, axis=(2, 3))

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        content = np.stack(docs.get_attributes('blob'))
        _input = torch.from_numpy(content.astype('float32'))
        _features = self._get_features(_input).detach()
        _features = _features.numpy()
        _features = self._get_pooling(_features)
        docs.embeddings = _features


class DocVectorIndexer(Executor):
    def __init__(self, index_file_name: str, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArrayMemmap(self.workspace + f'/{index_file_name}')

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        docs.match(
            self._docs,
            metric='cosine',
            normalization=(1, 0),
            limit=int(parameters['top_k']),
        )


class KeyValueIndexer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArrayMemmap(self.workspace + '/kv-idx')

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def query(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            for match in doc.matches:
                extracted_doc = self._docs[match.parent_id]
                match.update(extracted_doc)


class WeightedRanker(Executor):
    @requests(on='/search')
    def rank(
        self, docs_matrix: List['DocumentArray'], parameters: Dict, **kwargs
    ) -> 'DocumentArray':
        """
        :param docs_matrix: list of :class:`DocumentArray` on multiple requests to
          get bubbled up matches.
        :param parameters: the parameters passed into the ranker, in this case stores :attr`top_k`
          to filter k results based on score.
        :param kwargs: not used (kept to maintain interface)
        """

        result_da = DocumentArray()  # length: 1 as every time there is only one query
        for d_mod1, d_mod2 in zip(*docs_matrix):

            final_matches = {}  # type: Dict[str, Document]

            for m in d_mod1.matches:
                m.scores['relevance'] = m.scores['cosine'].value * d_mod1.weight
                final_matches[m.parent_id] = Document(m, copy=True)

            for m in d_mod2.matches:
                if m.parent_id in final_matches:
                    final_matches[m.parent_id].scores['relevance'] = final_matches[
                        m.parent_id
                    ].scores['relevance'].value + (
                        m.scores['cosine'].value * d_mod2.weight
                    )
                else:
                    m.scores['relevance'] = m.scores['cosine'].value * d_mod2.weight
                    final_matches[m.parent_id] = Document(m, copy=True)

            da = DocumentArray(list(final_matches.values()))
            da.sort(key=lambda ma: ma.scores['relevance'].value, reverse=True)
            d = Document(matches=da[: int(parameters['top_k'])])
            result_da.append(d)
        return result_da


def _move_channel_axis(
    img: 'np.ndarray', channel_axis_to_move: int, target_channel_axis: int = -1
) -> 'np.ndarray':
    """
    Ensure the color channel axis is the default axis.
    """
    if channel_axis_to_move == target_channel_axis:
        return img
    return np.moveaxis(img, channel_axis_to_move, target_channel_axis)


def _load_image(blob: 'np.ndarray', channel_axis: int):
    """
    Load an image array and return a `PIL.Image` object.
    """

    from PIL import Image

    img = _move_channel_axis(blob, channel_axis)
    return Image.fromarray(img.astype('uint8'))


def _crop_image(
    img,
    target_size: Union[Tuple[int, int], int],
    top: int = None,
    left: int = None,
    how: str = 'precise',
):
    """
    Crop the input :py:mod:`PIL` image.

    :param img: :py:mod:`PIL.Image`, the image to be resized
    :param target_size: desired output size. If size is a sequence like
        (h, w), the output size will be matched to this. If size is an int,
        the output will have the same height and width as the `target_size`.
    :param top: the vertical coordinate of the top left corner of the crop box.
    :param left: the horizontal coordinate of the top left corner of the crop box.
    :param how: the way of cropping. Valid values include `center`, `random`, and, `precise`. Default is `precise`.
        - `center`: crop the center part of the image
        - `random`: crop a random part of the image
        - `precise`: crop the part of the image specified by the crop box with the given ``top`` and ``left``.
        .. warning:: When `precise` is used, ``top`` and ``left`` must be fed valid value.

    """
    import PIL.Image as Image

    assert isinstance(img, Image.Image), 'img must be a PIL.Image'
    img_w, img_h = img.size
    if isinstance(target_size, int):
        target_h = target_w = target_size
    elif isinstance(target_size, Tuple) and len(target_size) == 2:
        target_h, target_w = target_size
    else:
        raise ValueError(
            f'target_size should be an integer or a tuple of two integers: {target_size}'
        )
    w_beg = left
    h_beg = top
    if how == 'center':
        w_beg = int((img_w - target_w) / 2)
        h_beg = int((img_h - target_h) / 2)
    elif how == 'random':
        w_beg = np.random.randint(0, img_w - target_w + 1)
        h_beg = np.random.randint(0, img_h - target_h + 1)
    elif how == 'precise':
        assert w_beg is not None and h_beg is not None
        assert (
            0 <= w_beg <= (img_w - target_w)
        ), f'left must be within [0, {img_w - target_w}]: {w_beg}'
        assert (
            0 <= h_beg <= (img_h - target_h)
        ), f'top must be within [0, {img_h - target_h}]: {h_beg}'
    else:
        raise ValueError(f'unknown input how: {how}')
    if not isinstance(w_beg, int):
        raise ValueError(f'left must be int number between 0 and {img_w}: {left}')
    if not isinstance(h_beg, int):
        raise ValueError(f'top must be int number between 0 and {img_h}: {top}')
    w_end = w_beg + target_w
    h_end = h_beg + target_h
    img = img.crop((w_beg, h_beg, w_end, h_end))
    return img, h_beg, w_beg


def _resize_short(img, target_size, how: str = 'LANCZOS'):
    """
    Resize the input :py:mod:`PIL` image.
    :param img: :py:mod:`PIL.Image`, the image to be resized
    :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
        this. If size is an int, the smaller edge of the image will be matched to this number maintain the aspect
        ratio.
    :param how: the interpolation method. Valid values include `NEAREST`, `BILINEAR`, `BICUBIC`, and `LANCZOS`.
        Default is `LANCZOS`. Please refer to `PIL.Image` for detaisl.
    """
    import PIL.Image as Image

    assert isinstance(img, Image.Image), 'img must be a PIL.Image'
    if isinstance(target_size, int):
        percent = float(target_size) / min(img.size[0], img.size[1])
        target_w = int(round(img.size[0] * percent))
        target_h = int(round(img.size[1] * percent))
    elif isinstance(target_size, Tuple) and len(target_size) == 2:
        target_h, target_w = target_size
    else:
        raise ValueError(
            f'target_size should be an integer or a tuple of two integers: {target_size}'
        )
    img = img.resize((target_w, target_h), getattr(Image, how))
    return img
