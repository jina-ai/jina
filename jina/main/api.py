__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


def pod(args):
    """Start a Pod"""
    from ..peapods import Pod
    with Pod(args) as p:
        p.join()


def pea(args):
    """Start a Pea"""
    from ..peapods import Pea
    try:
        with Pea(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


def gateway(args):
    """Start a Gateway Pod"""
    from ..peapods.pod import GatewayPod
    with GatewayPod(args) as fs:
        fs.join()


def log(args):
    """Receive piped log output and beautify the log"""
    from ..logging.pipe import PipeLogger
    PipeLogger(args).start()


def check(args):
    """Check jina config, settings, imports, network etc"""
    from .checker import ImportChecker
    ImportChecker(args)


def ping(args):
    from .checker import NetworkChecker
    NetworkChecker(args)


def client(args):
    """Start a client connects to the gateway"""
    from ..clients.python import PyClient
    PyClient(args)


def hello_world(args):
    from ..helloworld import hello_world
    hello_world(args)


def flow(args):
    """Start a Flow from a YAML file"""
    from ..flow import Flow
    if args.yaml_path:
        from threading import Event
        f = Flow.load_config(args.yaml_path)
        f._update_args(args)
        with f:

            try:
                Event().wait()
            except KeyboardInterrupt:
                pass
    else:
        from jina.logging import default_logger
        default_logger.critical('start a flow from CLI requires a valid "--yaml-path"')
