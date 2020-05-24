__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import json

from jina import __version__
from jina.clients.python import PyClient
from jina.helper import yaml
from jina.logging import default_logger
from jina.logging.pipe import PipeLogger
from jina.main.checker import ImportChecker, NetworkChecker
from jina.main.export import api_to_dict
from jina.peapods import Pod
from jina.peapods.pod import GatewayPod

from threading import Event


def pod(args):
    """Start a Pod"""
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
    with GatewayPod(args) as fs:
        fs.join()


def log(args):
    """Receive piped log output and beautify the log"""
    PipeLogger(args).start()


def check(args):
    """Check jina config, settings, imports, network etc"""
    ImportChecker(args)


def ping(args):
    NetworkChecker(args)


def client(args):
    """Start a client connects to the gateway"""
    PyClient(args)


def export_api(args):

    if args.yaml_path:
        for yp in args.yaml_path:
            f_name = (yp % __version__) if '%s' in yp else yp
            with open(f_name, 'w', encoding='utf8') as fp:
                yaml.dump(api_to_dict(), fp)
            default_logger.info(f'API is exported to {f_name}')

    if args.json_path:
        for jp in args.json_path:
            f_name = (jp % __version__) if '%s' in jp else jp
            with open(f_name, 'w', encoding='utf8') as fp:
                json.dump(api_to_dict(), fp, sort_keys=True)
            default_logger.info(f'API is exported to {f_name}')


def hello_world(args):
    from jina.helloworld import hello_world
    hello_world(args)


def flow(args):
    """Start a Flow from a YAML file"""
    from jina.flow import Flow
    if args.yaml_path:
        f = Flow.load_config(args.yaml_path)
        f._update_args(args)
        with f:
            f.block()
    else:
        default_logger.critical('start a flow from CLI requires a valid "--yaml-path"')
