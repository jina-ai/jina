from tests import JinaTestCase


class JinaImageTestCase(JinaTestCase):
    @staticmethod
    def create_test_image(output_fn, size=50):
        from PIL import Image
        image = Image.new('RGB', size=(size, size), color=(155, 0, 0))
        with open(output_fn, "wb") as f:
            image.save(f, 'jpeg')

    @staticmethod
    def create_test_img_array(img_height, img_width):
        import numpy as np
        return np.random.randint(0, 256, (img_height, img_width, 3))
