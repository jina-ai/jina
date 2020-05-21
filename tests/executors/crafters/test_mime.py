import glob

from jina.flow import Flow
from tests import JinaTestCase

num_docs = 100
image_src = '../../../**/*.png'


def input_fn():
    idx = 0
    for g in glob.glob(image_src, recursive=True)[:num_docs]:
        with open(g, 'rb') as fp:
            yield fp.read()
            idx += 1


class MyTestCase(JinaTestCase):
    def test_dummy_seg(self):
        f = Flow().add(yaml_path='!DataURICrafter\nwith: {mimetype: png}')
        with f:
            f.index(input_fn=input_fn(), output_fn=print)

        f = Flow().add(yaml_path='!DataURICrafter\nwith: {mimetype: png, base64: true}')
        with f:
            f.index(input_fn=input_fn(), output_fn=print)

    # def test_dummy_seg_random(self):
    #     f = Flow().add(yaml_path='../../yaml/dummy-seg-random.yml')
    #     with f:
    #         f.index(input_fn=random_docs(10), in_proto=True, output_fn=self.collect_chunk_id)
