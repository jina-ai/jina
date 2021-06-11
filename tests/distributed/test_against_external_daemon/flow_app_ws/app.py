import sys
from jina import Flow
from .helper import foo, bar


def main(port_expose):
    f = Flow(port_expose=port_expose).add()
    foo()
    bar()
    with f:
        f.block()


if __name__ == '__main__':
    port_expose = int(sys.argv[1])
    main(port_expose)
