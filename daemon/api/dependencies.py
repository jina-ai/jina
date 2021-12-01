import os
from pathlib import Path
from http import HTTPStatus
from contextlib import ExitStack
from typing import Dict, List, Optional

from pydantic import FilePath
from pydantic.errors import PathNotAFileError
from fastapi import HTTPException, UploadFile, File, Query, Depends

from jina import Flow, __docker_host__
from jina.helper import cached_property
from jina.peapods import CompoundPod
from jina.peapods.peas.helper import update_runtime_cls
from jina.peapods.runtimes.container.helper import get_gpu_device_requests
from jina.enums import (
    PeaRoleType,
    SocketType,
    RemoteWorkspaceState,
)
from .. import daemon_logger
from ..models.ports import Ports, PortMapping, PortMappings
from ..models import DaemonID, FlowModel, PodModel, PeaModel, GATEWAY_RUNTIME_DICT
from ..helper import get_workspace_path, change_cwd, change_env
from ..stores import workspace_store as store


class Environment:
    """Parses environment variables to be set inside the containers"""

    _split_char = '='
    _strip_chars = ''.join(['\r', '\n', '\t'])

    def __init__(self, envs: List[str] = Query([])) -> None:
        self.vars = {}
        self.validate(envs)

    def validate(self, envs: List[str]):
        """Validate and set env vars as a dict

        :param envs: list of env vars passed as query params
        """
        for env in envs:
            try:
                k, v = env.split(self._split_char)
                self.vars[k.strip(self._strip_chars)] = v.strip(self._strip_chars)
            except ValueError:
                daemon_logger.warning(
                    f'{env} doesn\'t follow required standard. please pass envs in `key{self._split_char}value` format'
                )
                continue


class FlowDepends:
    """Validates & Sets host/port dependencies during Flow creation/update"""

    def __init__(
        self,
        workspace_id: DaemonID,
        filename: str,
        envs: Environment = Depends(Environment),
    ) -> None:
        self.workspace_id = workspace_id
        self.filename = filename
        self.id = DaemonID('jflow')
        self.params = FlowModel(
            uses=self.filename, workspace_id=self.workspace_id.jid, identity=self.id
        )
        self.envs = envs.vars
        self._ports = {}
        self.load_and_dump()
        # Unlike `PeaModel` / `PodModel`, `gpus` arg doesn't exist in FlowModel
        # We try assigning `all` gpus to the Flow container by default.
        self.device_requests = get_gpu_device_requests('all')

    def localpath(self) -> Path:
        """Validates local filepath in workspace from filename.
        Raise 404 if filepath doesn't exist in workspace.

        :return: filepath for flow yaml
        """
        try:
            return FilePath.validate(
                Path(get_workspace_path(self.workspace_id, self.filename))
            )
        except PathNotAFileError as e:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'File `{self.filename}` not found in workspace `{self.workspace_id}`',
            )

    @property
    def newname(self) -> str:
        """Return newfile path in following format
        `flow.yml` -> `<root-workspace>/<workspace-id>/<flow-id>_flow.yml`
        `flow1.yml` -> `<root-workspace>/<workspace-id>/<flow-id>_flow1.yml`
        `src/flow.yml` -> `<root-workspace>/<workspace-id>/src/<flow-id>_flow.yml`
        `src/abc/flow.yml` -> `<root-workspace>/<workspace-id>/src/abc/<flow-id>_flow.yml`

        :return: newname for the flow yaml file
        """
        parts = Path(self.filename).parts
        if len(parts) == 1:
            return f'{self.id}_{self.filename}'
        else:
            return os.path.join(*parts[:-1], f'{self.id}_{parts[-1]}')

    @property
    def newfile(self) -> str:
        """Return newfile path fetched from newname

        :return: return filepath to save flow config in
        """
        return get_workspace_path(self.workspace_id, self.newname)

    def load_and_dump(self) -> None:
        """
        every Flow created inside JinaD lives inside a container. It is important to know the
        list of ports to be published with localhost before actually starting the container.

        1. `load` the flow yaml here.
            - yaml is stored in `workspace` directory, so we'll `cd` there
            - yaml might include env vars. so we'll set them (passed via query params)
        2. `build` the Flow so that `gateway` gets added.
            - get the list of ports to be published (port_expose, port_in, port_out, port_ctrl)
            - ports need to be published for gateway & executors that are not `ContainerRuntime` or `JinadRuntime` based
            - Pod level args for ports are enough, as we don't need to publish Pea ports
            - all the above Pods also run in docker, hence we set `runs_in_docker`
        3. `save` the Flow config.
            - saves port configs of all `executors` into the new yaml.
            - set `JINA_FULL_CLI` envvar, so that `gateway` args are also added.
            - save the config into a new file.
        4. pass this new file as filename to `partial-daemon` to start the Flow
        """
        with ExitStack() as stack:
            # set env vars
            stack.enter_context(change_env('JINA_FULL_CLI', 'true'))

            # change directory to `workspace`
            stack.enter_context(change_cwd(get_workspace_path(self.workspace_id)))

            # load and build
            f: Flow = Flow.load_config(
                str(self.localpath()), substitute=True, context=self.envs
            ).build()
            # get & set the ports mapping, set `runs_in_docker`
            port_mapping = []
            port_mapping.append(
                PortMapping(
                    pod_name='gateway',
                    pea_name='gateway',
                    ports=Ports(port_expose=f.port_expose),
                )
            )
            for pod_name, pod in f._pod_nodes.items():
                runtime_cls = update_runtime_cls(pod.args, copy=True).runtime_cls
                if isinstance(pod, CompoundPod):
                    if (
                        runtime_cls
                        in [
                            'ZEDRuntime',
                            'GRPCDataRuntime',
                            'ContainerRuntime',
                        ]
                        + list(GATEWAY_RUNTIME_DICT.values())
                    ):
                        # For a `CompoundPod`, publish ports for head Pea & tail Pea
                        # Check daemon.stores.partial.PartialFlowStore.add() for addtional logic
                        # to handle `CompoundPod` inside partial-daemon.
                        for pea_args in [pod.head_args, pod.tail_args]:
                            pea_args.runs_in_docker = False
                            self._update_port_mapping(pea_args, pod_name, port_mapping)
                else:
                    if runtime_cls in ['ZEDRuntime', 'GRPCDataRuntime'] + list(
                        GATEWAY_RUNTIME_DICT.values()
                    ):
                        pod.args.runs_in_docker = True
                        current_ports = Ports()
                        for port_name in Ports.__fields__:
                            setattr(
                                current_ports,
                                port_name,
                                getattr(pod.args, port_name, None),
                            )

                        port_mapping.append(
                            PortMapping(
                                pod_name=pod_name, pea_name='', ports=current_ports
                            )
                        )
                    elif (
                        runtime_cls in ['ContainerRuntime']
                        and hasattr(pod.args, 'replicas')
                        and pod.args.replicas > 1
                    ):
                        for pea_args in [pod.peas_args['head'], pod.peas_args['tail']]:
                            self._update_port_mapping(pea_args, pod_name, port_mapping)

            self.ports = port_mapping
            # save to a new file & set it for partial-daemon
            f.save_config(filename=self.newfile)
            self.params.uses = self.newname

    def _update_port_mapping(self, pea_args, pod_name, port_mapping):
        current_ports = Ports()
        for port_name in Ports.__fields__:
            # Get port from Namespace args & set to PortMappings
            setattr(
                current_ports,
                port_name,
                getattr(pea_args, port_name, None),
            )
        port_mapping.append(
            PortMapping(
                pod_name=pod_name,
                pea_name=pea_args.name,
                ports=current_ports,
            )
        )

    @property
    def ports(self) -> PortMappings:
        """getter for ports

        :return: ports to be mapped
        """
        return self._ports

    @ports.setter
    def ports(self, port_mapping: List[PortMapping]):
        """setter for ports

        :param port_mapping: port mapping
        """
        self._ports = PortMappings.parse_obj(port_mapping)


class PeaDepends:
    """Validates & Sets host/port dependencies during Pea creation/update"""

    def __init__(
        self,
        workspace_id: DaemonID,
        pea: PeaModel,
        envs: Environment = Depends(Environment),
    ):
        # Deepankar: adding quotes around PeaModel breaks things
        self.workspace_id = workspace_id
        self.params = pea
        self.id = DaemonID('jpea')
        self.envs = envs.vars
        self.validate()

    @property
    def host_in(self) -> str:
        """
        host_in for the pea/pod

        :return: host_in
        """
        # TAIL & SINGLETON peas are handled by dynamic routing
        return (
            __docker_host__
            if PeaRoleType.from_string(self.params.pea_role)
            in [PeaRoleType.PARALLEL, PeaRoleType.HEAD]
            else self.params.host_in
        )

    @property
    def host_out(self) -> str:
        """
        host_out for the pea/pod

        :return: host_out
        """
        # TAIL & SINGLETON peas are handled by dynamic routing
        return (
            __docker_host__
            if PeaRoleType.from_string(self.params.pea_role)
            in [PeaRoleType.PARALLEL, PeaRoleType.HEAD]
            else self.params.host_in
        )

    @cached_property
    def ports(self) -> Dict:
        """
        Determines ports to be mapped to dockerhost

        :return: dict of port mappings
        """
        _mapping = {
            'port_in': 'socket_in',
            'port_out': 'socket_out',
            'port_ctrl': 'socket_ctrl',
        }
        # Map only "bind" ports for HEAD, TAIL & SINGLETON
        if self.params.runtime_cls == 'ContainerRuntime':
            # For `ContainerRuntime`, port mapping gets handled internally
            return {}
        if PeaRoleType.from_string(self.params.pea_role) != PeaRoleType.PARALLEL:
            return {
                f'{getattr(self.params, i)}/tcp': getattr(self.params, i)
                for i in self.params.__fields__
                if i in _mapping
                and SocketType.from_string(
                    getattr(self.params, _mapping[i], 'PAIR_BIND')
                ).is_bind
            }
        else:
            return {f'{self.params.port_ctrl}/tcp': self.params.port_ctrl}

    def validate(self):
        """
        # TODO (deepankar): These docs would need changes after dynamic routing changes.
        Validates and sets arguments to be used in store
        DOCKER_HOST = 'host.docker.internal'

        SINGLETON
        =========
        `runtime_cls`: `ZEDRuntime`
            `host_in`, `host_out`: set to `DOCKER_HOST`, as it would talk to gateway/other pods
            `ports`: map `port_in` & `port_out` if `socket_in` & `socket_out` are BIND.
                     map `port_ctrl`, ignore `port_exppse`

        `runtime_cls`: `ContainerRuntime`
            `host_in`,`host_out`: don't change. Handled interally in `jina pod`
            `ports`: handled internally in `ContainerRuntime`

        PARALLEL
        ========
        `runtime_cls`: `ZEDRuntime`
            `host_in`, `host_out`: set to `DOCKERHOST`
                host config handled interally in `jina pod` wouldn't work here, as they need to talk to head/tail
                peas which are on `DOCKER_HOST`
            `ports`: don't map `port_in` & `port_out` as they're always CONNECT.
                     map `port_ctrl`??, ignore `port_exppse`

        `runtime_cls`: `ContainerRuntime` or `ZEDRuntime`
            `host_in`, `host_out`: set to `DOCKERHOST`
                host config handled interally in `jina pod` wouldn't work here, as they need to talk to head/tail
                peas which are on `DOCKER_HOST`
            `ports`: handled internally in `ContainerRuntime`

        HEAD/TAIL
        =========
        `runtime_cls`:  `ZEDRuntime` (always??)
            `host_in`, `host_out`: set to `DOCKER_HOST`, as they would talk to gateway/other pods.
            `ports`: map `port_in` & `port_out` if `socket_in` & `socket_out` are BIND.
                     map `port_ctrl`, ignore `port_exppse`

        TODO: check the host_in/host_out for CONNECT sockets
        TODO: HEAD/TAIL - can `uses_before` or `uses_after` be `docker://`
        """
        # Each pea is inside a container
        self.params.host_in = self.host_in
        self.params.host_out = self.host_out
        self.params.identity = self.id
        self.params.workspace_id = self.workspace_id
        self.params.runs_in_docker = True
        self.device_requests = (
            get_gpu_device_requests(self.params.gpus) if self.params.gpus else None
        )


class PodDepends(PeaDepends):
    """Validates & Sets host/port dependencies during Pod creation/update"""

    def __init__(
        self,
        workspace_id: DaemonID,
        pod: PodModel,
        envs: Environment = Depends(Environment),
    ):
        self.workspace_id = workspace_id
        self.params = pod
        self.id = DaemonID('jpod')
        self.envs = envs.vars
        self.validate()


class WorkspaceDepends:
    """Interacts with task queue to inform about workspace creation/update"""

    def __init__(
        self, id: Optional[DaemonID] = None, files: List[UploadFile] = File(None)
    ) -> None:
        self.id = id if id else DaemonID('jworkspace')
        self.files = files

        from ..tasks import __task_queue__

        if self.id not in store:
            # when id doesn't exist in store, create it.
            store.add(id=self.id, value=RemoteWorkspaceState.PENDING)
            __task_queue__.put((self.id, self.files))

        if self.id in store and store[self.id].state == RemoteWorkspaceState.ACTIVE:
            # when id exists in the store and is "active", update it.
            store.update(id=self.id, value=RemoteWorkspaceState.PENDING)
            __task_queue__.put((self.id, self.files))

        self.item = {self.id: store[self.id]}
