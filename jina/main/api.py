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


def flow(args):
    from ..flow.cli import FlowCLI
    FlowCLI(args)
