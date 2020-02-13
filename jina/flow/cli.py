from . import Flow


class FlowCLI(Flow):
    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(**vars(args))
