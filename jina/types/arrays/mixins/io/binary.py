import os.path
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
    def load_binary(cls: Type['T'], file: Union[str, BinaryIO, bytes]) -> 'T':
        """Load array elements from a LZ4-compressed binary file.

        :param file: File or filename or serialized bytes where the data is stored.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        elif isinstance(file, bytes):
            file_ctx = nullcontext(file)
        elif os.path.exists(file):
            file_ctx = open(file, 'rb')
        else:
            raise ValueError(f'unsupported input {file!r}')

        dap = jina_pb2.DocumentArrayProto()

        from ...document import DocumentArray
        import lz4.frame

        with file_ctx as fp:
            d = fp.read() if hasattr(fp, 'read') else fp
            dap.ParseFromString(lz4.frame.decompress(d))
            da = cls()
            da.extend(DocumentArray(dap.docs))
            return da

    def save_binary(self, file: Union[str, BinaryIO]) -> None:
        """Save array elements into a LZ4 compressed binary file.

        Comparing to :meth:`save_json`, it is faster and the file is smaller, but not human-readable.

        .. note::
            To get a binary presentation in memory, use ``bytes(...)``.

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
            fp.write(bytes(self))

    def to_bytes(self) -> bytes:
        """Serialize itself into bytes with LZ4 compression.

        For more Pythonic code, please use ``bytes(...)``.

        :return: the binary serialization in bytes
        """
        dap = jina_pb2.DocumentArrayProto()
        dap.docs.extend(self._pb_body)
        import lz4.frame

        return lz4.frame.compress(dap.SerializePartialToString())

    def __bytes__(self):
        return self.to_bytes()
