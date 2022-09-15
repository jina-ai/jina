import os
import subprocess
import tempfile
from pathlib import Path

import docker
import pytest
from pytest_kind import KindCluster

from jina.logging.logger import JinaLogger

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


class KindClusterWrapper:
    def __init__(self, kind_cluster: KindCluster, logger: JinaLogger):
        self._cluster = kind_cluster
        self._cluster.ensure_kubectl()
        self._kube_config_path = os.path.join(
            os.getcwd(), '.pytest-kind/pytest-kind/kubeconfig'
        )
        self._log = logger
        self._set_kube_config()
        self._install_linkderd(kind_cluster)
        self._loaded_images = set()

    def _linkerd_install_cmd(self, kind_cluster, cmd, tool_name):
        self._log.info(f'Installing {tool_name} to Cluster...')
        kube_out = subprocess.check_output(
            (str(kind_cluster.kubectl_path), 'version'),
            env=os.environ,
        )
        self._log.info(f'kuberbetes versions: {kube_out}')

        # since we need to pipe to commands and the linkerd output can bee too long
        # there is a risk of deadlock and hanging tests: https://docs.python.org/3/library/subprocess.html#popen-objects
        # to avoid this, the right mechanism is implemented in subprocess.run and subprocess.check_output, but output
        # must be piped to a file-like object, not to stdout
        proc_stdout = tempfile.TemporaryFile()
        proc = subprocess.run(
            cmd,
            stdout=proc_stdout,
            env={"KUBECONFIG": str(kind_cluster.kubeconfig_path)},
        )

        proc_stdout.seek(0)
        kube_out = subprocess.check_output(
            (
                str(kind_cluster.kubectl_path),
                'apply',
                '-f',
                '-',
            ),
            stdin=proc_stdout,
            env=os.environ,
        )

        returncode = proc.returncode
        self._log.info(
            f'Installing {tool_name} to Cluster returned code {returncode}, kubectl output was {kube_out}'
        )
        if returncode is not None and returncode != 0:
            raise Exception(f'Installing {tool_name} failed with {returncode}')

    def _install_linkderd(self, kind_cluster):
        # linkerd < 2.12: only linkerd install is needed
        # in later versions, linkerd install --crds will be needed
        self._linkerd_install_cmd(
            kind_cluster, [f'{Path.home()}/.linkerd2/bin/linkerd', 'install'], 'Linkerd'
        )

        self._log.info('check linkerd status')
        out = subprocess.check_output(
            [f'{Path.home()}/.linkerd2/bin/linkerd', 'check'],
            env=os.environ,
        )

        print(f'linkerd check yields {out.decode() if out else "nothing"}')

    def install_linkderd_smi(self):
        self._log.info('Installing Linkerd SMI to Cluster...')
        proc = subprocess.Popen(
            [f'{Path.home()}/.linkerd2/bin/linkerd-smi', 'install'],
            stdout=subprocess.PIPE,
            env={"KUBECONFIG": str(self._cluster.kubeconfig_path)},
        )
        kube_out = subprocess.check_output(
            (
                str(self._cluster.kubectl_path),
                'apply',
                '-f',
                '-',
            ),
            stdin=proc.stdout,
            env=os.environ,
        )
        self._log.info('Poll status of linkerd smi install')
        returncode = proc.poll()
        self._log.info(
            f'Installing Linkerd to Cluster returned code {returncode}, kubectl output was {kube_out}'
        )
        if returncode is not None and returncode != 0:
            raise Exception(f"Installing linkerd failed with {returncode}")

        self._log.info('check linkerd status')
        out = subprocess.check_output(
            [f'{Path.home()}/.linkerd2/bin/linkerd-smi', 'check'],
            env=os.environ,
        )

        print(f'linkerd check yields {out.decode() if out else "nothing"}')

    def _set_kube_config(self):
        self._log.info(f'Setting KUBECONFIG to {self._kube_config_path}')
        os.environ['KUBECONFIG'] = self._kube_config_path

    def load_docker_images(self, images, image_tag_map):
        for image in images:
            full_image_name = image + ':' + image_tag_map[image]
            if full_image_name not in self._loaded_images:
                if image != 'alpine' and image != 'jinaai/jina':
                    build_docker_image(image, image_tag_map)
                self._cluster.load_docker_image(full_image_name)
                self._loaded_images.add(full_image_name)


@pytest.fixture()
def test_dir() -> str:
    return cur_dir


@pytest.fixture
def logger():
    return JinaLogger('kubernetes-testing')


@pytest.fixture(scope='session')
def k8s_cluster(kind_cluster: KindCluster) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, JinaLogger('kubernetes-cluster-logger'))


@pytest.fixture
def image_name_tag_map():
    return {
        'reload-executor': '0.13.1',
        'test-executor': '0.13.1',
        'slow-process-executor': '0.14.1',
        'executor-merger': '0.1.1',
        'set-text-executor': '0.1.1',
        'failing-executor': '0.1.1',
        'jinaai/jina': 'test-pip',
    }


def build_docker_image(image_name, image_name_tag_map):
    logger = JinaLogger('kubernetes-testing')
    image_tag = image_name + ':' + image_name_tag_map[image_name]
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, image_name), tag=image_tag
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture(autouse=True)
def set_test_pip_version():
    os.environ['JINA_GATEWAY_IMAGE'] = 'jinaai/jina:test-pip'
    yield
    del os.environ['JINA_GATEWAY_IMAGE']


@pytest.fixture(autouse=True)
def load_cluster_config(k8s_cluster):
    import kubernetes

    try:
        # try loading kube config from disk first
        kubernetes.config.load_kube_config()
    except kubernetes.config.config_exception.ConfigException:
        # if the config could not be read from disk, try loading in cluster config
        # this works if we are running inside k8s
        kubernetes.config.load_incluster_config()


@pytest.fixture
def docker_images(request, image_name_tag_map, k8s_cluster):
    image_names = request.param
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    return images
