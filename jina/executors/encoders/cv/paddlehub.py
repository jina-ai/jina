import os
import numpy as np
from PIL import Image

from .. import BaseImageEncoder


class XCeptionPaddleImageEncoder(BaseImageEncoder):
    def __init__(self, model_name='xception71_imagenet', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.dim = 2048
        self.DATA_DIM = 224
        self.img_mean = np.array([0.485, 0.456, 0.406]).reshape((3, 1, 1))
        self.img_std = np.array([0.229, 0.224, 0.225]).reshape((3, 1, 1))

    def post_init(self):
        import paddlehub as hub
        import paddle.fluid as fluid
        module = hub.Module(name=self.model_name)
        self.inputs, self.outputs, self.model = module.context(trainable=False)
        place = fluid.CUDAPlace(int(os.getenv('FLAGS_selected_gpus', '0'))) if self.on_gpu else fluid.CPUPlace()
        self.exe = fluid.Executor(place)
        self.processor = module.processor

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        batch_data = []
        for idx in range(data.shape[0]):
            r = np.uint8(data[idx, :, :, :])
            processed_img = self.process_image(Image.fromarray(r))
            batch_data.append(processed_img)
        feature_map, *_ = self.exe.run(
            program=self.model,
            fetch_list=[
                self.outputs["feature_map"].name
            ],
            feed={
                self.inputs["image"].name: np.stack(batch_data, axis=0),
            },
            return_numpy=False
        )
        return np.array(feature_map).squeeze()

    def close(self):
        self.exe.close()

    def process_image(self, img):
        img = self.resize_short(img, target_size=256)
        img = self.crop_image(img, target_size=self.DATA_DIM, center=True)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = np.array(img).astype('float32').transpose((2, 0, 1)) / 255
        img -= self.img_mean
        img /= self.img_std
        return img

    @staticmethod
    def resize_short(img, target_size):
        percent = float(target_size) / min(img.size[0], img.size[1])
        resized_width = int(round(img.size[0] * percent))
        resized_height = int(round(img.size[1] * percent))
        img = img.resize((resized_width, resized_height), Image.LANCZOS)
        return img

    @staticmethod
    def crop_image(img, target_size, center):
        width, height = img.size
        size = target_size
        if center:
            w_start = (width - size) / 2
            h_start = (height - size) / 2
        else:
            w_start = np.random.randint(0, width - size + 1)
            h_start = np.random.randint(0, height - size + 1)
        w_end = w_start + size
        h_end = h_start + size
        img = img.crop((w_start, h_start, w_end, h_end))
        return img
