from docarray import Document
from jina import Flow


def run():
    f = Flow().add(uses='executor1/config.yml')
    # or load from Flow YAML
    # f = Flow.load_config('flow.yml')
    with f:
        da = f.post('/', [Document(), Document()])
        print(da.texts)


if __name__ == '__main__':
    run()
    # or run in terminal:
    # $ jina flow --uses flow.yml
