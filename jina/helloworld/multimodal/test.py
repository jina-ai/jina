from jina.helloworld.multimodal.app import hello_world
from jina.parsers.helloworld import set_hw_multimodal_parser

if __name__ == '__main__':
    args = set_hw_multimodal_parser().parse_args()
    hello_world(args)
