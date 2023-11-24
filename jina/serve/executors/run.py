import argparse
import multiprocessing
import os
import copy
from typing import Dict, Optional, Type, Union, TYPE_CHECKING

from jina.logging.logger import JinaLogger
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.helper import _get_workspace_from_name_and_shards
from jina.constants import RAFT_TO_EXECUTOR_PORT

if TYPE_CHECKING:
    import threading


def run_raft(
        args: 'argparse.Namespace',
        is_ready: Union['multiprocessing.Event', 'threading.Event'],
):
    """Method to run the RAFT

    This method is the target for the Pod's `thread` or `process`

    :param args: namespace args from the Pod
    :param is_ready: concurrency event to communicate Executor runtime is ready to receive messages
    """

    import jraft

    def pascal_case_dict(d):
        new_d = {}
        for key, value in d.items():
            new_key = key
            if '_' in key:
                new_key = ''.join(word.capitalize() for word in key.split('_'))
            new_d[new_key] = value
        return new_d

    raft_id = str(args.replica_id)
    shard_id = args.shard_id if args.shards > 1 else -1

    raft_dir = _get_workspace_from_name_and_shards(
        workspace=args.workspace, name='raft', shard_id=shard_id
    )

    port = args.port[0] if isinstance(args.port, list) else args.port
    address = f'{args.host}:{port}'
    executor_target = f'{args.host}:{port + RAFT_TO_EXECUTOR_PORT}'

    # if the Executor was already persisted, retrieve its port and host configuration
    logger = JinaLogger(context=f'RAFT-{args.name}', **vars(args))
    persisted_address = jraft.get_configuration(raft_id, raft_dir)
    if persisted_address:
        logger.debug(f'Configuration found on the node: Address {persisted_address}')
        address = persisted_address
        executor_host, port = persisted_address.split(':')
        executor_target = f'{executor_host}:{int(port) + 1}'

    raft_configuration = pascal_case_dict(args.raft_configuration or {})
    log_level = raft_configuration.get('LogLevel', os.getenv('JINA_LOG_LEVEL', 'INFO'))
    raft_configuration['LogLevel'] = log_level
    is_ready.wait()
    logger.debug(f'Will run the RAFT node with RAFT configuration {raft_configuration}')
    jraft.run(
        address,
        raft_id,
        raft_dir,
        args.name,
        executor_target,
        **raft_configuration,
    )


def run(
        args: 'argparse.Namespace',
        name: str,
        runtime_cls: Type[AsyncNewLoopRuntime],
        envs: Dict[str, str],
        is_started: Union['multiprocessing.Event', 'threading.Event'],
        is_shutdown: Union['multiprocessing.Event', 'threading.Event'],
        is_ready: Union['multiprocessing.Event', 'threading.Event'],
        is_signal_handlers_installed: Union['multiprocessing.Event', 'threading.Event'],
        jaml_classes: Optional[Dict] = None,
):
    """Method representing the :class:`BaseRuntime` activity.

    This method is the target for the Pod's `thread` or `process`

    .. note::
        :meth:`run` is running in subprocess/thread, the exception can not be propagated to the main process.
        Hence, please do not raise any exception here.

    .. note::
        Please note that env variables are process-specific. Subprocess inherits envs from
        the main process. But Subprocess's envs do NOT affect the main process. It does NOT
        mess up user local system envs.

    .. warning::
        If you are using ``thread`` as backend, envs setting will likely be overidden by others

    .. note::
        `jaml_classes` contains all the :class:`JAMLCompatible` classes registered in the main process.
        When using `spawn` as the multiprocessing start method, passing this argument to `run` method re-imports
        & re-registers all `JAMLCompatible` classes.

    :param args: namespace args from the Pod
    :param name: name of the Pod to have proper logging
    :param runtime_cls: the runtime class to instantiate
    :param envs: a dictionary of environment variables to be set in the new Process
    :param is_started: concurrency event to communicate runtime is properly started. Used for better logging
    :param is_shutdown: concurrency event to communicate runtime is terminated
    :param is_ready: concurrency event to communicate runtime is ready to receive messages
    :param is_signal_handlers_installed: concurrency event to communicate runtime is ready to get SIGTERM from orchestration
    :param jaml_classes: all the `JAMLCompatible` classes imported in main process
    """
    req_handler_cls = None
    if runtime_cls == 'GatewayRuntime':
        from jina.serve.runtimes.gateway.request_handling import GatewayRequestHandler
        req_handler_cls = GatewayRequestHandler
    elif runtime_cls == 'WorkerRuntime':
        from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler
        req_handler_cls = WorkerRequestHandler
    elif runtime_cls == 'HeadRuntime':
        from jina.serve.runtimes.head.request_handling import HeaderRequestHandler
        req_handler_cls = HeaderRequestHandler

    logger = JinaLogger(name, **vars(args))

    def _unset_envs():
        if envs:
            for k in envs.keys():
                os.environ.pop(k, None)

    def _set_envs():
        if args.env:
            os.environ.update({k: str(v) for k, v in envs.items()})

    try:
        _set_envs()

        runtime = AsyncNewLoopRuntime(
            args=args,
            req_handler_cls=req_handler_cls,
            gateway_load_balancer=getattr(args, 'gateway_load_balancer', False),
            signal_handlers_installed_event=is_signal_handlers_installed
        )
    except Exception as ex:
        logger.error(
            f'{ex!r} during {runtime_cls!r} initialization'
            + f'\n add "--quiet-error" to suppress the exception details'
            if not args.quiet_error
            else '',
            exc_info=not args.quiet_error,
        )
    else:
        if not is_shutdown.is_set():
            is_started.set()
            with runtime:
                # here the ready event is being set
                is_ready.set()
                runtime.run_forever()
    finally:
        _unset_envs()
        is_shutdown.set()
        logger.debug('process terminated')


def run_stateful(args: 'argparse.Namespace',
                 name: str,
                 runtime_cls: Type[AsyncNewLoopRuntime],
                 envs: Dict[str, str]):
    """
    Method to be called in Docker containers when Stateful Executor is required. This will start
    2 processes in the Docker container.
    :param args: namespace args from the Pod
    :param name: name of the Pod to have proper logging
    :param runtime_cls: the runtime class to instantiate
    :param envs: a dictionary of environment variables to be set in the new Process
    """
    import signal
    from jina.jaml import JAML
    is_ready = multiprocessing.Event()
    is_shutdown = multiprocessing.Event()
    is_started = multiprocessing.Event()
    is_signal_handlers_installed = multiprocessing.Event()
    raft_worker = multiprocessing.Process(
        target=run_raft,
        kwargs={
            'args': args,
            'is_ready': is_ready,
        },
        name=name,
        daemon=True,
    )
    cargs = copy.deepcopy(args)

    from jina.constants import RAFT_TO_EXECUTOR_PORT

    if isinstance(cargs.port, int):
        cargs.port += RAFT_TO_EXECUTOR_PORT
    elif isinstance(cargs.port, list):
        cargs.port = [port + RAFT_TO_EXECUTOR_PORT for port in cargs.port]
    worker = multiprocessing.Process(
        target=run,
        kwargs={
            'args': cargs,
            'name': name,
            'envs': envs,
            'is_started': is_started,
            'is_shutdown': is_shutdown,
            'is_ready': is_ready,
            'is_signal_handlers_installed': is_signal_handlers_installed,
            'runtime_cls': runtime_cls,
            'jaml_classes': JAML.registered_classes(),
        },
        name=name,
        daemon=False,
    )

    try:
        HANDLED_SIGNALS = (
            signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
            signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
            signal.SIGSEGV,
        )

        def signal_handler(*args, **kwargs):
            worker.terminate()
            raft_worker.terminate()

        for sig in HANDLED_SIGNALS:
            signal.signal(sig, signal_handler)

        worker.start()
        raft_worker.start()

        worker.join()
        raft_worker.join()
    except:
        worker.terminate()
        raft_worker.terminate()
