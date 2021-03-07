__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

if False:
    from argparse import Namespace


def pod(args: 'Namespace'):
    """Start a Pod"""
    from jina.peapods import Pod

    try:
        with Pod(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


def pea(args: 'Namespace'):
    """Start a Pea"""
    from jina.peapods import Pea

    try:
        with Pea(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


def gateway(args: 'Namespace'):
    """Start a Gateway Pod"""
    pod(args)


def check(args: 'Namespace'):
    """Check jina config, settings, imports, network etc"""
    from jina.checker import ImportChecker

    ImportChecker(args)


def ping(args: 'Namespace'):
    from jina.checker import NetworkChecker

    NetworkChecker(args)


def client(args: 'Namespace'):
    """Start a client connects to the gateway"""
    from jina.clients import Client

    Client(args)


def export_api(args: 'Namespace'):
    import json
    from .export import api_to_dict
    from jina.jaml import JAML
    from jina import __version__
    from jina.logging import default_logger
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


def hello_world(args: 'Namespace'):
    from jina.helloworld.fashion import hello_world

    hello_world(args)


def hello(args: 'Namespace'):
    if args.hello == 'fashion':
        from jina.helloworld.fashion import hello_world
    elif args.hello == 'chatbot':
        from jina.helloworld.chatbot import hello_world
    elif args.hello == 'multimodal':
        from jina.helloworld.multimodal import hello_world
    else:
        raise ValueError(f'must be one of [`fashion`, `chatbot`, `multimodal`]')

    hello_world(args)


def flow(args: 'Namespace'):
    """Start a Flow from a YAML file or a docker image"""
    from jina.flow import Flow

    if args.uses:
        f = Flow.load_config(args.uses)
        with f:
            f.block()
    else:
        from jina.logging import default_logger

        default_logger.critical('start a flow from CLI requires a valid "--uses"')


def optimizer(args: 'Namespace'):
    """Start an optimization from a YAML file"""
    from jina.optimizers import run_optimizer_cli

    run_optimizer_cli(args)


def hub(args: 'Namespace'):
    """Start a hub builder for build, push, pull"""
    from jina.docker.hubio import HubIO

    getattr(HubIO(args), args.hub)()
