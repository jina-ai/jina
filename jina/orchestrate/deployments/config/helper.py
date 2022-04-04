import os

from jina import __default_executor__, __version__
from jina.enums import PodRoleType
from jina.hubble.helper import parse_hub_uri
from jina.hubble.hubio import HubIO


def get_image_name(uses: str) -> str:
    """The image can be provided in different formats by the user.
    This function converts it to an image name which can be understood by k8s.
    It uses the Hub api to get the image name and the latest tag on Docker Hub.

    If you don't want to rebuild image on Jina Hub,
    you can set `JINA_HUB_NO_IMAGE_REBUILD` environment variable.

    :param uses: image name

    :return: normalized image name
    """
    try:
        rebuild_image = 'JINA_HUB_NO_IMAGE_REBUILD' not in os.environ
        scheme, name, tag, secret = parse_hub_uri(uses)
        meta_data, _ = HubIO.fetch_meta(
            name, tag, secret=secret, rebuild_image=rebuild_image, force=True
        )
        image_name = meta_data.image_name
        return image_name
    except Exception:
        if uses.startswith('docker'):
            # docker:// is a valid requirement and user may want to put its own image
            return uses.replace('docker://', '')
        raise


def to_compatible_name(name: str) -> str:
    """Converts the deployment name to a valid name for K8s and docker compose.

    :param name: name of the deployment
    :return: compatible name
    """
    return name.replace('/', '-').replace('_', '-').lower()


def get_base_executor_version():
    """
    Get the version of jina to be used
    :return: the version tag
    """
    import requests

    try:
        url = 'https://registry.hub.docker.com/v1/repositories/jinaai/jina/tags'
        tags = requests.get(url).json()
        name_set = {tag['name'] for tag in tags}
        if __version__ in name_set:
            return __version__
        else:
            return 'master'
    except:
        return 'master'


def construct_runtime_container_args(cargs, uses_metas, uses_with, pod_type):
    """
    Construct a set of Namespace arguments into a list of arguments to pass to a container entrypoint
    :param cargs: The namespace arguments
    :param uses_metas: The uses_metas to override
    :param uses_with: The uses_with to override
    :param pod_type: The pod_type
    :return: Arguments to pass to container
    """
    import json

    from jina.helper import ArgNamespace
    from jina.parsers import set_pod_parser

    taboo = {
        'uses_with',
        'uses_metas',
        'volumes',
        'uses_before',
        'uses_after',
        'workspace_id',
        'upload_files',
        'noblock_on_start',
    }

    if pod_type == PodRoleType.HEAD:
        taboo.add('uses')
        taboo.add('workspace')

    if pod_type in {PodRoleType.WORKER, PodRoleType.GATEWAY}:
        taboo.add('polling')

    non_defaults = ArgNamespace.get_non_defaults_args(
        cargs,
        set_pod_parser(),
        taboo=taboo,
    )
    _args = ArgNamespace.kwargs2list(non_defaults)
    container_args = ['executor'] + _args
    if uses_metas is not None:
        container_args.extend(['--uses-metas', json.dumps(uses_metas)])
    if uses_with is not None:
        container_args.extend(['--uses-with', json.dumps(uses_with)])
    container_args.append('--native')
    return container_args


def validate_uses(uses: str):
    """Validate uses argument

    :param uses: uses argument
    :return: boolean indicating whether is a valid uses to be used in K8s or docker compose
    """
    if uses == __default_executor__ or uses.startswith('docker://'):
        return True

    try:
        scheme, _, _, _ = parse_hub_uri(uses)
        if scheme in {'jinahub+docker', 'jinahub+sandbox'}:
            return True
    except ValueError:
        return False
