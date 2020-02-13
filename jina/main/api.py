def pod(args):
    """Start a Pod"""
    from ..peapods.pod import Pod
    with Pod(args) as p:
        p.join()


def frontend(args):
    """Start a frontend"""
    from jina.peapods.pod import FrontendPod
    with FrontendPod(args) as fs:
        fs.join()


def log(args):
    """Receive piped log output and beautify the log"""
    from ..logging.pipe import PipeLogger
    PipeLogger(args).start()


def check(args):
    """Check jina config, settings, imports, network etc"""
    from .checker import ImportChecker, NetworkChecker
    if args.check == 'import':
        ImportChecker(args)
    elif args.check == 'network':
        NetworkChecker(args)


def client(args):
    """Start a client connects to the frontend"""
    from ..clients.python import PyClient
    PyClient(args)
