import sys
from jina import Flow
from executors import TinyDBIndexer, SklearnExecutor


def main(port):
    f = Flow(port=port).add(uses=TinyDBIndexer).add(uses=SklearnExecutor)
    with f:
        f.block()


if __name__ == '__main__':
    port = int(sys.argv[1])
    main(port)
