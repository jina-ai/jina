from ....hubble.helper import parse_hub_uri
from ....hubble.hubio import HubIO


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
