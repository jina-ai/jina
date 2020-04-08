import numpy as np
import numbers

from .. import BaseChunkCrafter


class ImageChunkCrafter(BaseChunkCrafter):

    def __init__(self, channel_axis: int = -1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis

    def _load_image(self, blob: 'np.ndarray'):
        from PIL import Image
        img = self.check_channel_axis(blob)
        return Image.fromarray(img.astype('uint8'))

    def check_channel_axis(self, img: 'np.ndarray'):
        if self.channel_axis != -1:
            img = np.moveaxis(img, self.channel_axis, -1)
        return img


    @staticmethod
    def _resize_short(img, target_size, how='LANCZOS'):
        import PIL.Image as Image
        percent = float(target_size) / min(img.size[0], img.size[1])
        resized_width = int(round(img.size[0] * percent))
        resized_height = int(round(img.size[1] * percent))
        img = img.resize((resized_width, resized_height), getattr(Image, how))
        return img

    @staticmethod
    def _crop_image(img, target_size, left=None, top=None, how='precise'):
        img_width, img_height = img.size
        width, height = target_size
        w_start = left
        h_start = top
        if how == 'center':
            w_start = (img_width - width) / 2
            h_start = (img_height - height) / 2
        elif how == 'random':
            w_start = np.random.randint(0, img_width - width + 1)
            h_start = np.random.randint(0, img_height - height + 1)
        if not isinstance(w_start, numbers.Number):
            raise ValueError('left must be int number between 0 and {}: {}'.format(img_width, left))
        if not isinstance(h_start, numbers.Number):
            raise ValueError('top must be int number between 0 and {}: {}'.format(img_height, top))
        w_end = w_start + width
        h_end = h_start + height
        img = img.crop((w_start, h_start, w_end, h_end))
        return img

