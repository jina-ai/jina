from . import Flow

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class FlowCLI(Flow):
    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(**vars(args))
