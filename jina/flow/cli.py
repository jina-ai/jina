from . import Flow

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class FlowCLI:
    def __init__(self, args: 'argparse.Namespace'):
        with open(args.flow_yaml_path) as fp:
            fl = Flow.load_config(fp)
