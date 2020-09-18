from .. import ImageResizer


def create_random_img_array(img_height, img_width):
    import numpy as np
    return np.random.randint(0, 256, (img_height, img_width, 3))


def test_resize():
    img_width = 20
    img_height = 17
    output_dim = 71
    crafter = ImageResizer(target_size=output_dim)
    img_array = create_random_img_array(img_width, img_height)
    crafted_doc = crafter.craft(img_array)
    assert min(crafted_doc['blob'].shape[:-1]) == output_dim
