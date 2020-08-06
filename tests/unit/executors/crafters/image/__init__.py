from tests import JinaTestCase


class JinaImageTestCase(JinaTestCase):
    @staticmethod
    def create_test_image(output_fn, size_width=50, size_height=50):
        from PIL import Image
        image = Image.new('RGB', size=(size_width, size_height), color=(155, 0, 0))
        with open(output_fn, "wb") as f:
            image.save(f, 'jpeg')

    @staticmethod
    def create_random_img_array(img_height, img_width):
        import numpy as np
        return np.random.randint(0, 256, (img_height, img_width, 3))

    @staticmethod
    def create_test_img_array():
        import numpy as np
        img = np.array([i for i in range(100)]).reshape(10, 10)
        return np.repeat(img[:, :, np.newaxis], 3, axis=2)
