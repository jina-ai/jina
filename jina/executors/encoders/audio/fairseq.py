__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseAudioEncoder
from ..frameworks import BaseTorchEncoder
from ...decorators import batching, as_ndarray


class Wav2VecSpeechEncoder(BaseTorchEncoder, BaseAudioEncoder):
    """
    :class:`Wav2VecSpeechEncoder` is a speech encoder based on `wav2vec` - unsupervised pre-training for speech
    recognition presented and implemented by Facebook: https://github.com/pytorch/fairseq/tree/master/examples/wav2vec
    :class:`Wav2VecSpeechEncoder` uses a pre-trained model to encode an audio signal from a `Batch x Signal Length`
    ndarray into a `Batch x Concatenated Features` ndarray.
    """

    def __init__(self, model_path: str, input_sample_rate: int = 22050, *args, **kwargs):
        """
        Wav2vec model produces a representation for each time step at a rate of 100 Hz.

        :param model_path: the path of the pre-trained model. The pre-trained model can be downloaded at
            https://github.com/pytorch/fairseq/blob/master/examples/Wav2Vec/README.md#pre-trained-models
        :param input_sample_rate: input sampling rate in Hz (22050 by default)
        """
        super().__init__(*args, **kwargs)
        self.model_path = model_path
        self.input_sample_rate = input_sample_rate

    def post_init(self):
        import torch
        from fairseq.models.wav2vec import Wav2VecModel
        cp = torch.load(self.model_path, map_location=torch.device('cpu'))
        self.model = Wav2VecModel.build_model(cp['args'], task=None)
        self.model.load_state_dict(cp['model'])
        self.model.eval()
        self.to_device(self.model)
        self._sess_func = None
        self._tensor_func = torch.tensor

    @batching
    @as_ndarray
    def encode(self, data: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        Resamples the input audio signal to 16kHz, segments the resampled signal of each Chunk into wav2vec frames,
        encodes the frames and concatenates Chunk frame embeddings into a single Chunk embedding.

        :param data: a `Batch x Signal Length` ndarray, where `Signal Length` is a number of samples
        :return: a `Batch x Concatenated Features` ndarray, where `Concatinated Features` is a 512-dimensional feature
        vector times the number of the wav2vec frames
        """
        assert data.shape[1] >= 465, 'the signal must have at least 465 samples'
        from librosa import resample
        embeds = []
        with self.session():
            for chunk_data in data:
                resampled_signal = resample(chunk_data, self.input_sample_rate, 16000)
                signal_tensor = self.array2tensor(resampled_signal.reshape(1, -1))
                features = self.model.feature_extractor(signal_tensor)
                embed_tensor = self.model.feature_aggregator(features)[0]
                chunk_embed = self.tensor2array(embed_tensor).T.flatten()
                embeds.append(chunk_embed)
        return embeds

    def array2tensor(self, array):
        tensor = self._tensor_func(array)
        return tensor.cuda() if self.on_gpu else tensor

    def tensor2array(self, tensor):
        return tensor.cuda().numpy() if self.on_gpu else tensor.numpy()

    @property
    def session(self):
        if self._sess_func is None:
            self._sess_func = self.get_session()
        return self._sess_func

    def get_session(self):
        from torch import no_grad
        return no_grad
