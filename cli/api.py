__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


def pod(args):
    """Start a Pod"""
    from jina.peapods import Pod
    with Pod(args) as p:
        p.join()


def pea(args):
    """Start a Pea"""
    from jina.peapods import Pea
    try:
        with Pea(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


def gateway(args):
    """Start a Gateway Pod"""
    from jina.peapods.pod import GatewayPod
    with GatewayPod(args) as fs:
        fs.join()


def log(args):
    """Receive piped log output and beautify the log"""
    from jina.logging.pipe import PipeLogger
    PipeLogger(args).start()


def check(args):
    """Check jina config, settings, imports, network etc"""
    from jina.checker import ImportChecker
    ImportChecker(args)


def ping(args):
    from jina.checker import NetworkChecker
    NetworkChecker(args)


def client(args):
    """Start a client connects to the gateway"""
    from jina.clients.python import PyClient
    PyClient(args)


def export_api(args):
    from .export import api_to_dict
    from jina import __version__
    from jina.logging import default_logger

    if args.yaml_path:
        for yp in args.yaml_path:
            f_name = (yp % __version__) if '%s' in yp else yp
            from jina.helper import yaml
            with open(f_name, 'w', encoding='utf8') as fp:
                yaml.dump(api_to_dict(), fp)
            default_logger.info(f'API is exported to {f_name}')

    if args.json_path:
        for jp in args.json_path:
            f_name = (jp % __version__) if '%s' in jp else jp
            import json
            with open(f_name, 'w', encoding='utf8') as fp:
                json.dump(api_to_dict(), fp, sort_keys=True)
            default_logger.info(f'API is exported to {f_name}')


def hello_world(args):
    from jina.helloworld import hello_world
    hello_world(args)


def flow(args):
    """Start a Flow from a YAML file or a docker image"""
    from jina.flow import Flow
    if args.uses:
        f = Flow.load_config(args.uses)
        with f:
            f.block()
    else:
        from jina.logging import default_logger
        default_logger.critical('start a flow from CLI requires a valid "--uses"')


def hub(args):
    """Start a hub builder for build, push, pull"""
    from jina.docker.hubio import HubIO
    getattr(HubIO(args), args.hub)()

