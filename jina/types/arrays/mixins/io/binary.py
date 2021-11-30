from contextlib import nullcontext
from typing import Union, BinaryIO, TYPE_CHECKING, Type

from ..... import __windows__
from .....proto import jina_pb2

if TYPE_CHECKING:
    from ...document import DocumentArray
    from .....helper import T


class BinaryIOMixin:
    """Save/load an array to a binary file. """

    @classmethod
    def load_binary(cls: Type['T'], file: Union[str, BinaryIO]) -> 'T':
        """Load array elements from a binary file.

        :param file: File or filename to which the data is saved.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'rb')

        dap = jina_pb2.DocumentArrayProto()

        from ...document import DocumentArray

        with file_ctx as fp:
            dap.ParseFromString(fp.read())
            da = cls()
            da.extend(DocumentArray(dap.docs))
            return da

    def save_binary(self, file: Union[str, BinaryIO]) -> None:
        """Save array elements into a binary file.

        Comparing to :meth:`save_json`, it is faster and the file is smaller, but not human-readable.

        :param file: File or filename to which the data is saved.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            if __windows__:
                file_ctx = open(file, 'wb', newline='')
            else:
                file_ctx = open(file, 'wb')

        with file_ctx as fp:
            dap = jina_pb2.DocumentArrayProto()
            if self._pb_body:
                dap.docs.extend(self._pb_body)
            fp.write(dap.SerializePartialToString())
