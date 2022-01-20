from jina import __version__
from jina.hubble.helper import parse_hub_uri
from jina.hubble.hubio import HubIO


def get_image_name(uses: str) -> str:
    """The image can be provided in different formats by the user.
    This function converts it to an image name which can be understood by k8s.
    It uses the Hub api to get the image name and the latest tag on Docker Hub.
    :param uses: image name

    :return: normalized image name
    """
    try:
        scheme, name, tag, secret = parse_hub_uri(uses)
        meta_data, _ = HubIO.fetch_meta(name, tag, secret=secret, force=True)
        image_name = meta_data.image_name
        return image_name
    except Exception:
        if uses.startswith('docker'):
            # docker:// is a valid requirement and user may want to put its own image
            return uses.replace('docker://', '')
        raise


def to_compatible_name(name: str) -> str:
    """Converts the pod name to a valid name for K8s and docker compose.

    :param name: name of the pod
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
