import sys
from jina import Flow
from executors import TinyDBIndexer, SklearnExecutor


def main(port_expose):
    f = Flow(port_expose=port_expose).add(uses=TinyDBIndexer).add(uses=SklearnExecutor)
    with f:
        f.block()


if __name__ == '__main__':
    port_expose = int(sys.argv[1])
    main(port_expose)
