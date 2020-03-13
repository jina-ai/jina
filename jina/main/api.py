def pod(args):
    """Start a Pod"""
    from ..peapods.pod import get_pod
    with get_pod(args) as p:
        p.join()


def pea(args):
    """Start a Pea"""
    from ..peapods.pea import get_pea
    with get_pea(args) as p:
        p.join()


def frontend(args):
    """Start a frontend"""
    from ..peapods.pod import FrontendPod
    with FrontendPod(args) as fs:
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
    """Start a client connects to the frontend"""
    from ..clients.python import PyClient
    PyClient(args)


def flow(args):
    from ..flow.cli import FlowCLI
    FlowCLI(args)
