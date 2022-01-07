# Executor in Action

## Fastai

This `Executor` uses the [ResNet18](https://docs.fast.ai) network for object classification on images provided
by [fastai](https://github.com/fastai/fastai).

The `encode` function of this executor generates a feature vector for each image in each `Document` of the
input `DocumentArray`. The feature vector generated is the output activations of the neural network (a vector of 1000
components). 

````{admonition} Note
:class: note
The embedding of each text is performed in a joined operation (all embeddings are created for all
images in a single function call) to achieve higher performance.
````

As a result each `Document` in the input `DocumentArray`  _docs_ will have an `embedding` after `encode()` has
completed.

```python
import torch
from fastai.vision.models import resnet18

from jina import Executor, requests


class ResnetImageEncoder(Executor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = resnet18()
        self.model.eval()

    @requests
    def encode(self, docs, **kwargs):
        batch = torch.Tensor(docs.get_attributes('blob'))
        with torch.no_grad():
            batch_embeddings = self.model(batch).detach().numpy()

        for doc, emb in zip(docs, batch_embeddings):
            doc.embedding = emb

```

## Pytorch Lightning

This code snippet uses an autoencoder pretrained from cifar10-resnet18 to build an executor that encodes Document blob(
an ndarray that could for example be an image) into embedding . It demonstrates the use of prebuilt model
from [PyTorch Lightning Bolts](https://pytorch-lightning.readthedocs.io/en/stable/ecosystem/bolts.html) to build a Jina
encoder."

```python
from pl_bolts.models.autoencoders import AE

from jina import Executor, requests

import torch


class PLMwuAutoEncoder(Executor):
    def __init__(self, **kwargs):
        super().__init__()
        self.ae = AE(input_height=32).from_pretrained('cifar10-resnet18')
        self.ae.freeze()

    @requests
    def encode(self, docs, **kwargs):
        with torch.no_grad():
            for doc in docs:
                input_tensor = torch.from_numpy(doc.blob)
                output_tensor = self.ae(input_tensor)
                doc.embedding = output_tensor.detach().numpy()
```

## Paddle

The example below uses the PaddlePaddle [Ernie](https://github.com/PaddlePaddle/ERNIE) model as the encoder. The
Executor loads the pre-trained Ernie tokenizer and model, converts Jina Documents' ``doc.text`` into Paddle Tensors and
encodes the text as embeddings. As a result, each `Document` in the `DocumentArray` will have an `embedding` after
`encode()` has completed.

```python
import paddle as P  # paddle==2.1.0
import numpy as np
from ernie.modeling_ernie import ErnieModel  # paddle-ernie 0.2.0.dev1
from ernie.tokenizing_ernie import ErnieTokenizer

from jina import Executor, requests


class PaddleErineExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()
        self.tokenizer = ErnieTokenizer.from_pretrained('ernie-1.0')
        self.model = ErnieModel.from_pretrained('ernie-1.0')
        self.model.eval()

    @requests
    def encode(self, docs, **kwargs):
        for doc in docs:
            ids, _ = self.tokenizer.encode(doc.text)
            ids = P.to_tensor(np.expand_dims(ids, 0))
            pooled, encoded = self.model(ids)
            doc.embedding = pooled.numpy()
```

## Tensorflow

This `Executor` uses the [MobileNetV2](https://keras.io/api/applications/mobilenet/) network for object classification
on images.

It extracts the `buffer` field (which is the actual byte array) from each input `Document` in the `DocumentArray` _docs_
, preprocesses the byte array and uses _MobileNet_ to predict the classes (dog/car/...) found in the image. Those
predictions are Numpy arrays encoding the probability for each class supported by the model (1000 in this case).
The `Executor` stores those arrays then in the `embedding` for each `Document`.

As a result each `Document` in the input `DocumentArray` _docs_ will have an `embedding` after `encode()` has completed.

```python
import numpy as np
import tensorflow as tf
from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.python.framework.errors_impl import InvalidArgumentError

from jina import Executor, requests


class TfMobileNetEncoder(Executor):
    def __init__(self, **kwargs):
        super().__init__()
        self.image_dim = 224
        self.model = MobileNetV2(pooling='avg', input_shape=(self.image_dim, self.image_dim, 3))

    @requests
    def encode(self, docs, **kwargs):
        buffers, docs = docs.get_attributes_with_docs('buffer')

        tensors = [tf.io.decode_image(contents=b, channels=3) for b in buffers]
        resized_tensors = preprocess_input(np.array(self._resize_images(tensors)))

        embeds = self.model.predict(np.stack(resized_tensors))
        for d, b in zip(docs, embeds):
            d.embedding = b

    def _resize_images(self, tensors):
        resized_tensors = []
        for t in tensors:
            try:
                resized_tensors.append(tf.keras.preprocessing.image.smart_resize(t, (self.image_dim, self.image_dim)))
            except InvalidArgumentError:
                # this can happen if you include empty or other malformed images
                pass
        return resized_tensors
```

## MindSpore

The code snippet below takes ``docs`` as input and perform matrix multiplication with ``self.encoding_matrix``. It
leverages Mindspore ``Tensor`` conversion and operation. Finally, the ``embedding`` of each document will be set as the
multiplied result as ``np.ndarray``.

```python
import numpy as np
from mindspore import Tensor  # mindspore 1.2.0
import mindspore.ops as ops
import mindspore.context as context

from jina import Executor, requests


class MindsporeMwuExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()
        context.set_context(mode=context.PYNATIVE_MODE, device_target='CPU')
        self.encoding_mat = Tensor(np.random.rand(5, 5))

    @requests
    def encode(self, docs, **kwargs):
        matmul = ops.MatMul()
        for doc in docs:
            input_tensor = Tensor(doc.blob)  # convert the ``ndarray`` of the doc to ``Tensor``
            output_tensor = matmul(self.encoding_mat, input_tensor)  # multiply the input with the encoding matrix.
            doc.embedding = output_tensor.asnumpy()  # assign the encoding results to ``embedding``
```

## Scikit-learn

This `Executor` uses
a [TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
feature vector to generate sparse embeddings for text search.

The class `TFIDFTextEncoder` extracts stores a `tfidf_vectorizer` object that it is fitted with a dataset already
present in `sklearn`. The executor provides an `encode` method that receives a `DocumentArray` and updates each document
in the  `DocumentArray` with an `embedding` attribute that is the tf-idf representation of the text found in the
document.

````{admonition} Note
:class: note
The embedding of each text is perfomed in a joined operation (all embeddings are creted for all texts in
a single function call) to achieve higher performance.
````

As a result, each `Document` in the `DocumentArray` will have an `embedding` after `encode()` has completed.

```python
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer

from jina import Executor, requests, DocumentArray


class TFIDFTextEncoder(Executor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from sklearn import datasets

        dataset = fetch_20newsgroups()
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_vectorizer.fit(dataset.data)
        self.ttfidf_vectorizer = tfidf_vectorizer

    @requests
    def encode(self, docs: DocumentArray, *args, **kwargs):
        iterable_of_texts = docs.get_attributes('text')
        embedding_matrix = self.tfidf_vectorizer.transform(iterable_of_texts)

        for i, doc in enumerate(docs):
            doc.embedding = embedding_matrix[i]
```

## PyTorch

The code snippet below takes ``docs`` as input and perform feature extraction with ``modelnet v2``. It leverages
Pytorch's ``Tensor`` conversion and operation. Finally, the ``embedding`` of each document will be set as the extracted
features.

```python
import torch  # 1.8.1
import torchvision.models as models  # 0.9.1
from jina import Executor, requests


class PytorchMobilNetExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()
        self.model = models.quantization.mobilenet_v2(pretrained=True, quantize=True)
        self.model.eval()

    @requests
    def encode(self, docs, **kwargs):
        blobs = torch.Tensor(docs.get_attributes('blob'))
        with torch.no_grad():
            embeds = self.model(blobs).detach().numpy()
            for doc, embed in zip(docs, embeds):
                doc.embedding = embed
```

## ONNX

The code snippet bellow converts a `Pytorch` model to the `ONNX` and leverage `onnxruntime` to run inference tasks on
models from `hugging-face transformers`.

```python
from pathlib import Path

import numpy as np
import onnxruntime
from jina import Executor, requests
from transformers import BertTokenizerFast, convert_graph_to_onnx


class ONNXBertExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()

        # export your huggingface model to onnx
        convert_graph_to_onnx.convert(
            framework="pt",
            model="bert-base-cased",
            output=Path("onnx/bert-base-cased.onnx"),
            opset=11,
        )

        # create the tokenizer
        self.tokenizer = BertTokenizerFast.from_pretrained("bert-base-cased")

        # create the inference session
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = 1  # have an impact on performances
        options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        )

        # Load the model as a graph and prepare the CPU backend
        self.session = onnxruntime.InferenceSession(
            "onnx/bert-base-cased.onnx", options
        )
        self.session.disable_fallback()

    @requests
    def encode(self, docs, **kwargs):
        for doc in docs:
            tokens = self.tokenizer.encode_plus(doc.text)
            inputs = {name: np.atleast_2d(value) for name, value in tokens.items()}

            output, pooled = self.session.run(None, inputs)
            # assign the encoding results to ``embedding``
            doc.embedding = pooled[0]
```
