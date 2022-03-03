import os
from contextlib import ExitStack
from http import HTTPStatus
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException, UploadFile, File, Query, Depends
from pydantic import FilePath
from pydantic.errors import PathNotAFileError

from jina.orchestrate.pods.container_helper import get_gpu_device_requests
from jina.orchestrate.pods.helper import update_runtime_cls
from jina import Flow
from jina.enums import (
    RemoteWorkspaceState,
    PodRoleType,
)
from jina.helper import cached_property

from daemon import daemon_logger
from daemon.helper import get_workspace_path, change_cwd, change_env
from daemon.models import (
    DaemonID,
    FlowModel,
    DeploymentModel,
    PodModel,
    GATEWAY_RUNTIME_DICT,
)
from daemon.models.ports import Ports, PortMapping, PortMappings
from daemon.stores import workspace_store as store


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
        self.params = FlowModel(uses=self.filename, workspace_id=self.workspace_id.jid)
        self.envs = envs.vars
        self._ports = {}
        self.load_and_dump()
        # Unlike `PodModel` / `DeploymentModel`, `gpus` arg doesn't exist in FlowModel
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
            - get the list of ports to be published
            - ports need to be published for gateway & executors that are not `ContainerRuntime` or `JinadRuntime` based
            - Deployment level args for ports are enough, as we don't need to publish Pod ports
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
                    deployment_name='gateway',
                    pod_name='gateway',
                    ports=Ports(port=f.port),
                )
            )
            for deployment_name, deployment in f._deployment_nodes.items():
                runtime_cls = update_runtime_cls(deployment.args, copy=True).runtime_cls
                if runtime_cls in ['WorkerRuntime'] + list(
                    GATEWAY_RUNTIME_DICT.values()
                ):
                    current_ports = Ports()
                    for port_name in Ports.__fields__:
                        setattr(
                            current_ports,
                            port_name,
                            getattr(deployment.args, port_name, None),
                        )

                    port_mapping.append(
                        PortMapping(
                            deployment_name=deployment_name,
                            pod_name='',
                            ports=current_ports,
                        )
                    )
                elif (
                    runtime_cls in ['ContainerRuntime']
                    and hasattr(deployment.args, 'replicas')
                    and deployment.args.replicas > 1
                ):
                    for pod_args in [deployment.pod_args['head']]:
                        self._update_port_mapping(
                            pod_args, deployment_name, port_mapping
                        )

            self.ports = port_mapping
            # save to a new file & set it for partial-daemon
            f.save_config(filename=self.newfile)
            self.params.uses = self.newname

    def _update_port_mapping(self, pod_args, deployment_name, port_mapping):
        current_ports = Ports()
        for port_name in Ports.__fields__:
            # Get port from Namespace args & set to PortMappings
            setattr(
                current_ports,
                port_name,
                getattr(pod_args, port_name, None),
            )
        port_mapping.append(
            PortMapping(
                deployment_name=deployment_name,
                pod_name=pod_args.name,
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


class PodDepends:
    """Validates & Sets host/port dependencies during Pod creation/update"""

    def __init__(
        self,
        workspace_id: DaemonID,
        pod: PodModel,
        envs: Environment = Depends(Environment),
    ):
        # Deepankar: adding quotes around PodModel breaks things
        self.workspace_id = workspace_id
        self.params = pod
        self.id = DaemonID('jpod')
        self.envs = envs.vars
        self.update_args()

    @cached_property
    def ports(self) -> Dict:
        """
        Determines ports to be mapped to dockerhost

        :return: dict of port mappings
        """
        # Container pods are started in separate docker containers, so we should not expose port here
        if (
            (
                self.params.pod_role
                and PodRoleType.from_string(self.params.pod_role) != PodRoleType.HEAD
            )
            and self.params.uses
            and self.params.uses.startswith('docker://')
        ):
            return {}
        else:
            return {f'{self.params.port}/tcp': self.params.port}

    def update_args(self):
        """TODO: update docs"""
        # Each pod is inside a container
        self.params.workspace_id = self.workspace_id
        self.device_requests = (
            get_gpu_device_requests(self.params.gpus) if self.params.gpus else None
        )


class DeploymentDepends(PodDepends):
    """Validates & Sets host/port dependencies during Pod creation/update"""

    def __init__(
        self,
        workspace_id: DaemonID,
        deployment: DeploymentModel,
        envs: Environment = Depends(Environment),
    ):
        self.workspace_id = workspace_id
        self.params = deployment
        self.id = DaemonID('jdeployment')
        self.envs = envs.vars
        self.update_args()


class WorkspaceDepends:
    """Interacts with task queue to inform about workspace creation/update"""

    def __init__(
        self, id: Optional[DaemonID] = None, files: List[UploadFile] = File(None)
    ) -> None:
        self.id = id if id else DaemonID('jworkspace')
        self.files = files

        from daemon.tasks import __task_queue__

        if self.id not in store:
            # when id doesn't exist in store, create it.
            store.add(id=self.id, value=RemoteWorkspaceState.PENDING)
            __task_queue__.put((self.id, self.files))

        if self.id in store and store[self.id].state == RemoteWorkspaceState.ACTIVE:
            # when id exists in the store and is "active", update it.
            store.update(id=self.id, value=RemoteWorkspaceState.PENDING)
            __task_queue__.put((self.id, self.files))

        self.item = {self.id: store[self.id]}
