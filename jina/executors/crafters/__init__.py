__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Union, List

from .. import BaseExecutor


class BaseCrafter(BaseExecutor):
    """
    A :class:`BaseCrafter` transforms the content of `Document`.
    It can be used for preprocessing, segmenting etc.
    It is an interface for Crafters which is a family of executors intended to apply
    transformations to single documents.
    The apply function is :func:`craft`, where the name of the arguments will be used as keys of the content.

    :param args: Additional positional arguments which are just used for the parent initialization
    :param kwargs: Additional keyword arguments which are just used for the parent initialization
    """

    def craft(self, *args, **kwargs) -> Union[List[Dict], Dict]:
        """
        Apply function of this executor.
        The name of the arguments are used as keys, which are then used to tell :class:`Driver` what information to extract
        from the protobuf request accordingly.
        The name of the arguments should be always valid keys defined in the protobuf.

        :param args: Extra variable length arguments
        :param kwargs: Extra variable keyword arguments
        """
        raise NotImplementedError
