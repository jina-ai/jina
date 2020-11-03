import glob
import os

from jina.flow import Flow

num_docs = 100


def input_fn(pattern='../../**/*.png'):
    idx = 0
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        with open(g, 'rb') as fp:
            yield fp.read()
            idx += 1


def input_fn2(pattern='../*.*'):
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        yield g


def input_fn3():
    for g in [
        os.path.abspath(__file__),  # local file
        'https://github.com/jina-ai/jina/raw/master/.github/1500%D1%85667.gif?raw=true',
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
        'https://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/240px-001Bulbasaur.png']:
        yield g


def test_dummy_seg():
    f = Flow().add(uses='- !Buffer2URI | {mimetype: png}')
    with f:
        f.index(input_fn=input_fn)

    f = Flow().add(uses='- !Buffer2URI | {mimetype: png, base64: true}')
    with f:
        f.index(input_fn=input_fn)


def test_any_file():
    f = Flow().add(uses='- !URI2DataURI | {base64: true}')
    with f:
        f.index(input_fn=input_fn2)


def test_aba():
    f = (Flow().add(uses='- !Buffer2URI | {mimetype: png}')
         .add(uses='- !URI2Buffer {}')
         .add(uses='- !Buffer2URI | {mimetype: png}'))

    with f:
        f.index(input_fn=input_fn)


def test_pathURI2Buffer():
    f = (Flow().add(uses='- !URI2Buffer {}')
         .add(uses='- !Buffer2URI {}'))

    with f:
        f.index(input_fn=input_fn3)


def test_text2datauri():
    f = (Flow().add(uses='- !Text2URI {}'))

    with f:
        f.index_lines(lines=['abc', '123', 'hello, world'])


def test_gateway_dataui():
    f = (Flow().add(uses='_pass'))

    with f:
        f.index_lines(lines=['abc', '123', 'hello, world'])
