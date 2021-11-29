import json
from contextlib import nullcontext
from typing import Union, TextIO, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from .....helper import T


class JsonIOMixin:
    """Save/load a array into a JSON file."""

    def save_json(self, file: Union[str, TextIO]) -> None:
        """Save array elements into a JSON file.

        Comparing to :meth:`save_binary`, it is human-readable but slower to save/load and the file size larger.

        :param file: File or filename to which the data is saved.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'w')

        with file_ctx as fp:
            for d in self:
                json.dump(d.dict(), fp)
                fp.write('\n')

    @classmethod
    def load_json(cls: Type['T'], file: Union[str, TextIO]) -> 'T':
        """Load array elements from a JSON file.

        :param file: File or filename to which the data is saved.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file)

        from ....document import Document

        with file_ctx as fp:
            da = cls()
            da.extend(Document(v) for v in fp)
            return da
