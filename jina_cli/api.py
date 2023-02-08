from typing import TYPE_CHECKING

from jina.parsers.helper import _update_gateway_args

if TYPE_CHECKING:
    from argparse import Namespace


def deployment(args: 'Namespace'):
    """
    Start a Deployment

    :param args: arguments coming from the CLI.
    """
    from jina.orchestrate.deployments import Deployment

    if args.uses:
        dep = Deployment.load_config(args.uses)
        with dep:
            dep.block()
    else:
        raise ValueError('starting a Deployment from CLI requires a valid `--uses`')


def pod(args: 'Namespace'):
    """
    Start a Pod

    :param args: arguments coming from the CLI.
    """
    from jina.orchestrate.pods.factory import PodFactory

    try:
        with PodFactory.build_pod(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


def executor_native(args: 'Namespace'):
    """
    Starts an Executor in a WorkerRuntime

    :param args: arguments coming from the CLI.
    """

    if args.runtime_cls == 'WorkerRuntime':
        from jina.serve.runtimes.worker import WorkerRuntime

        runtime_cls = WorkerRuntime
    elif args.runtime_cls == 'HeadRuntime':
        from jina.serve.runtimes.head import HeadRuntime

        runtime_cls = HeadRuntime
    else:
        raise RuntimeError(
            f' runtime_cls {args.runtime_cls} is not supported with `--native` argument. `WorkerRuntime` is supported'
        )

    with runtime_cls(args) as rt:
        name = (
            rt._worker_request_handler._executor.metas.name
            if hasattr(rt, '_worker_request_handler')
            else rt.name
        )
        rt.logger.info(f'Executor {name} started')
        rt.run_forever()


def executor(args: 'Namespace'):
    """
    Starts an Executor in any Runtime

    :param args: arguments coming from the CLI.

    :returns: return the same as `pod` or `worker_runtime`
    """
    args.host = args.host[0]
    args.port = args.port[0]
    args.port_monitoring = args.port_monitoring[0]

    if args.native:
        return executor_native(args)
    else:
        return pod(args)


def worker_runtime(args: 'Namespace'):
    """
    Starts a WorkerRuntime

    :param args: arguments coming from the CLI.
    """
    from jina.serve.runtimes.worker import WorkerRuntime

    with WorkerRuntime(args) as runtime:
        runtime.logger.info(
            f'Executor {runtime._worker_request_handler._executor.metas.name} started'
        )
        runtime.run_forever()


def gateway(args: 'Namespace'):
    """
    Start a Gateway Deployment

    :param args: arguments coming from the CLI.
    """
    from jina.serve.runtimes import get_runtime

    args.port_monitoring = args.port_monitoring[0]
    _update_gateway_args(args)

    runtime_cls = get_runtime('GatewayRuntime')

    with runtime_cls(args) as runtime:
        runtime.logger.info(f'Gateway started')
        runtime.run_forever()


def ping(args: 'Namespace'):
    """
    Check the connectivity of a Pod

    :param args: arguments coming from the CLI.
    """
    from jina.checker import NetworkChecker

    NetworkChecker(args)


def dryrun(args: 'Namespace'):
    """
    Check the health of a Flow

    :param args: arguments coming from the CLI.
    """
    from jina.checker import dry_run_checker

    dry_run_checker(args)


def client(args: 'Namespace'):
    """
    Start a client connects to the gateway

    :param args: arguments coming from the CLI.
    """
    from jina.clients import Client

    Client(args)


def export(args: 'Namespace'):
    """
    Export the API

    :param args: arguments coming from the CLI.
    """
    from jina import exporter

    getattr(exporter, f'export_{args.export.replace("-", "_")}')(args)


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
        raise ValueError('starting a Flow from CLI requires a valid `--uses`')


def hub(args: 'Namespace'):
    """
    Start a hub builder for push, pull
    :param args: arguments coming from the CLI.
    """
    from hubble.executor.hubio import HubIO

    getattr(HubIO(args), args.hub_cli)()


def new(args: 'Namespace'):
    """
    Create a new jina project
    :param args:  arguments coming from the CLI.
    """
    import os
    import shutil

    from jina.constants import __resources_path__

    shutil.copytree(
        os.path.join(__resources_path__, 'project-template'), os.path.abspath(args.name)
    )


def help(args: 'Namespace'):
    """
    Lookup the usage of certain argument in Jina API.

    :param args: arguments coming from the CLI.
    """
    from jina_cli.lookup import lookup_and_print

    lookup_and_print(args.query.lower())


def auth(args: 'Namespace'):
    """
    Authenticate a user
    :param args: arguments coming from the CLI.
    """
    from hubble import api

    getattr(api, args.auth_cli.replace('-', '_'))(args)


def cloud(args: 'Namespace'):
    """
    Use jcloud (Jina Cloud) commands
    :param args: arguments coming from the CLI.
    """
    from jcloud import api

    getattr(api, args.jc_cli.replace('-', '_'))(args)
