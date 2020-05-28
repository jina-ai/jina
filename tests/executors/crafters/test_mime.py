import glob

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


def input_fn3():
    for g in ['test_mime.py',  # local file
              'https://github.com/jina-ai/jina/raw/master/.github/1500%D1%85667.gif?raw=true',
              'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
              'https://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/240px-001Bulbasaur.png']:
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
            f.index(input_fn=input_fn2, output_fn=print)

    def test_aba(self):
        f = (Flow().add(yaml_path='!Buffer2DataURI\nwith: {mimetype: png}')
             .add(yaml_path='DataURI2Buffer')
             .add(yaml_path='!Buffer2DataURI\nwith: {mimetype: png}'))

        with f:
            f.index(input_fn=input_fn, output_fn=print)

    def test_any2buffer(self):
        f = (Flow().add(yaml_path='Any2Buffer')
             .add(yaml_path='Buffer2DataURI'))

        with f:
            f.index(input_fn=input_fn3, output_fn=print)

    # def test_dummy_seg_random(self):
    #     f = Flow().add(yaml_path='../../yaml/dummy-seg-random.yml')
    #     with f:
    #         f.index(input_fn=random_docs(10), output_fn=self.collect_chunk_id)
