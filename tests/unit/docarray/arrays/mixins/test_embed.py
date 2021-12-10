import os

import numpy as np
import onnxruntime
import paddle
import pytest
import tensorflow as tf
import torch

from jina import DocumentArray, DocumentArrayMemmap

random_embed_models = {
    'keras': lambda: tf.keras.Sequential(
        [tf.keras.layers.Dropout(0.5), tf.keras.layers.BatchNormalization()]
    ),
    'pytorch': lambda: torch.nn.Sequential(
        torch.nn.Dropout(0.5), torch.nn.BatchNorm1d(128)
    ),
    'paddle': lambda: paddle.nn.Sequential(
        paddle.nn.Dropout(0.5), paddle.nn.BatchNorm1D(128)
    ),
}
cur_dir = os.path.dirname(os.path.abspath(__file__))
torch.onnx.export(
    random_embed_models['pytorch'](),
    torch.rand(1, 128),
    os.path.join(cur_dir, 'test-net.onnx'),
    do_constant_folding=True,  # whether to execute constant folding for optimization
    input_names=['input'],  # the model's input names
    output_names=['output'],  # the model's output names
    dynamic_axes={
        'input': {0: 'batch_size'},  # variable length axes
        'output': {0: 'batch_size'},
    },
)

random_embed_models['onnx'] = lambda: onnxruntime.InferenceSession(
    os.path.join(cur_dir, 'test-net.onnx')
)


@pytest.mark.parametrize('framework', ['onnx', 'keras', 'pytorch', 'paddle'])
@pytest.mark.parametrize('da', [DocumentArray, DocumentArrayMemmap])
@pytest.mark.parametrize('N', [2, 1000])
@pytest.mark.parametrize('batch_size', [1, 256])
@pytest.mark.parametrize('to_numpy', [True, False])
def test_embedding_on_random_network(framework, da, N, batch_size, to_numpy):
    docs = da.empty(N)
    docs.blobs = np.random.random([N, 128]).astype(np.float32)
    embed_model = random_embed_models[framework]()
    docs.embed(embed_model, batch_size=batch_size, to_numpy=to_numpy)

    r = docs.embeddings
    if hasattr(r, 'numpy'):
        r = r.numpy()
    embed1 = r.copy()

    # reset
    docs.embeddings = np.random.random([N, 128]).astype(np.float32)

    # try it again, it should yield the same result
    docs.embed(embed_model, batch_size=batch_size, to_numpy=to_numpy)
    np.testing.assert_array_almost_equal(docs.embeddings, embed1)

    # reset
    docs.embeddings = np.random.random([N, 128]).astype(np.float32)

    # now do this one by one
    docs[: int(N / 2)].embed(embed_model, batch_size=batch_size, to_numpy=to_numpy)
    docs[-int(N / 2) :].embed(embed_model, batch_size=batch_size, to_numpy=to_numpy)
    np.testing.assert_array_almost_equal(docs.embeddings, embed1)
