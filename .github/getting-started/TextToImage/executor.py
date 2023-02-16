import numpy as np

from jina import DocumentArray, Executor, requests


class TextToImage(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        import torch
        from diffusers import StableDiffusionPipeline

        self.pipe = StableDiffusionPipeline.from_pretrained(
            "CompVis/stable-diffusion-v1-4", torch_dtype=torch.float16
        ).to("cuda")

    @requests
    def generate_image(self, docs: DocumentArray, **kwargs):
        images = self.pipe(
            docs.texts
        ).images  # image here is in [PIL format](https://pillow.readthedocs.io/en/stable/)
        for i, doc in enumerate(docs):
            doc.tensor = np.array(images[i])
