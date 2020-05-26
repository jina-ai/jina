import glob

from jina.enums import ClientInputType
from jina.flow import Flow
from tests import JinaTestCase

num_docs = 100


def input_fn(pattern='../../../**/*.png'):
    idx = 0
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        with open(g, 'rb') as fp:
            yield fp.read()
            idx += 1


def input_fn2(pattern='../../*.*'):
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        yield g


class MyTestCase(JinaTestCase):
    def test_dummy_seg(self):
        f = Flow().add(yaml_path='!Buffer2DataURI\nwith: {mimetype: png}')
        with f:
            f.index(input_fn=input_fn(), output_fn=print)

        f = Flow().add(yaml_path='!Buffer2DataURI\nwith: {mimetype: png, base64: true}')
        with f:
            f.index(input_fn=input_fn(), output_fn=print)

    def test_any_file(self):
        f = Flow().add(yaml_path='!FilePath2DataURI\nwith: {base64: true}')
        with f:
            f.index(input_fn=input_fn2, output_fn=print, input_type=ClientInputType.FILE_PATH)

    def test_aba(self):
        f = (Flow().add(yaml_path='!Buffer2DataURI\nwith: {mimetype: png}')
             .add(yaml_path='DataURI2Buffer')
             .add(yaml_path='!Buffer2DataURI\nwith: {mimetype: png}'))

        with f:
            f.index(input_fn=input_fn, output_fn=print)

    # def test_dummy_seg_random(self):
    #     f = Flow().add(yaml_path='../../yaml/dummy-seg-random.yml')
    #     with f:
    #         f.index(input_fn=random_docs(10), input_type=ClientInputType.PROTOBUF, output_fn=self.collect_chunk_id)
