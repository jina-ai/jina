if False:
    from argparse import Namespace


def pod(args: 'Namespace'):
    """
    Start a Pod

    :param args: arguments coming from the CLI.
    """
    from jina.peapods.pods.factory import PodFactory

    try:
        with PodFactory.build_pod(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


# alias
executor = pod


def pea(args: 'Namespace'):
    """
    Start a Pea

    :param args: arguments coming from the CLI.
    """
    from jina.peapods import Pea

    try:
        with Pea(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


def gateway(args: 'Namespace'):
    """
    Start a Gateway Pod

    :param args: arguments coming from the CLI.
    """
    pod(args)


def ping(args: 'Namespace'):
    """
    Check the connectivity of a Pea

    :param args: arguments coming from the CLI.
    """
    from jina.checker import NetworkChecker

    NetworkChecker(args)


def client(args: 'Namespace'):
    """
    Start a client connects to the gateway

    :param args: arguments coming from the CLI.
    """
    from jina.clients import Client

    Client(args)


def export_api(args: 'Namespace'):
    """
    Export the API

    :param args: arguments coming from the CLI.
    """
    import json
    from .export import api_to_dict
    from jina.jaml import JAML
    from jina import __version__
    from jina.logging.predefined import default_logger
    from jina.schemas import get_full_schema

    if args.yaml_path:
        dump_api = api_to_dict()
        for yp in args.yaml_path:
            f_name = (yp % __version__) if '%s' in yp else yp
            with open(f_name, 'w', encoding='utf8') as fp:
                JAML.dump(dump_api, fp)
            default_logger.info(f'API is exported to {f_name}')

    if args.json_path:
        dump_api = api_to_dict()
        for jp in args.json_path:
            f_name = (jp % __version__) if '%s' in jp else jp
            with open(f_name, 'w', encoding='utf8') as fp:
                json.dump(dump_api, fp, sort_keys=True)
            default_logger.info(f'API is exported to {f_name}')

    if args.schema_path:
        dump_api = get_full_schema()
        for jp in args.schema_path:
            f_name = (jp % __version__) if '%s' in jp else jp
            with open(f_name, 'w', encoding='utf8') as fp:
                json.dump(dump_api, fp, sort_keys=True)
            default_logger.info(f'API is exported to {f_name}')


def hello(args: 'Namespace'):
    """
    Run any of the hello world examples

    :param args: arguments coming from the CLI.
    """
    if args.hello == 'fashion':
        from jina.helloworld.fashion.app import hello_world

        hello_world(args)
    elif args.hello == 'chatbot':
        from jina.helloworld.chatbot.app import hello_world

        hello_world(args)
    elif args.hello == 'multimodal':
        from jina.helloworld.multimodal.app import hello_world

        hello_world(args)
    elif args.hello == 'fork':
        from jina.helloworld.fork import fork_hello

        fork_hello(args)
    else:
        raise ValueError(f'must be one of [`fashion`, `chatbot`, `multimodal`, `fork`]')


def flow(args: 'Namespace'):
    """
    Start a Flow from a YAML file or a docker image

    :param args: arguments coming from the CLI.
    """
    from jina import Flow

    if args.uses:
        f = Flow.load_config(args.uses)
        with f:
            f.block()
    else:
        raise ValueError('start a flow from CLI requires a valid `--uses`')


def optimizer(args: 'Namespace'):
    """
    Start an optimization from a YAML file

    :param args: arguments coming from the CLI.
    """
    from jina.optimizers import run_optimizer_cli

    run_optimizer_cli(args)
