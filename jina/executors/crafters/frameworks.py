from jina.executors.crafters import BaseSegmenter
from jina.executors.devices import TorchDevice


class BaseTorchSegmenter(TorchDevice, BaseSegmenter):

    def __init__(self, model_name: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name

    def post_init(self):
        super().post_init()
        self._device = None

    @property
    def run_on_gpu(self):
        return self.on_gpu