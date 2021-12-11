from typing import TYPE_CHECKING, Union

from ...helper import T, deprecate_by, typename
from ...ndarray import get_array_type

if TYPE_CHECKING:
    from ...ndarray import ArrayType

    DocumentContentType = Union[bytes, str, ArrayType]

_DIGEST_SIZE = 8


class ContentPropertyMixin:
    """Provide helper functions for :class:`Document` to allow universal content property access. """

    @property
    def content(self) -> 'DocumentContentType':
        """Return the content of the document. It checks whichever field among :attr:`blob`, :attr:`text`,
        :attr:`buffer` has value and return it.

        .. seealso::
            :attr:`blob`, :attr:`buffer`, :attr:`text`

        :return: the value of the content depending on `:meth:`content_type`
        """
        attr = self.content_type
        if attr:
            return getattr(self, attr)

    @content.setter
    def content(self, value: 'DocumentContentType'):
        """Set the content of the document. It assigns the value to field with the right type.

        .. seealso::
            :attr:`blob`, :attr:`buffer`, :attr:`text`

        :param value: the value from which to set the content of the Document
        """
        if isinstance(value, bytes):
            self.buffer = value
        elif isinstance(value, str):
            self.text = value
        else:
            try:
                get_array_type(value)
                self.blob = value
            except:
                raise TypeError(f'{typename(value)} is not recognizable')

    @property
    def content_type(self) -> str:
        """Return the content type of the document, possible values: text, blob, buffer

        :return: the type of content of this Document
        """
        return self._pb_body.WhichOneof('content')

    @property
    def content_hash(self) -> str:
        """Get the document hash according to its content.

        :return: the unique hash code to represent this Document
        """
        # a tuple of field names that inclusive when computing content hash.
        from google.protobuf.field_mask_pb2 import FieldMask
        from hashlib import blake2b

        fields = (
            'text',
            'blob',
            'buffer',
            'embedding',
            'uri',
            'tags',
            'mime_type',
            'granularity',
            'adjacency',
        )
        masked_d = self._PbMsg()
        present_fields = {
            field_descriptor.name for field_descriptor, _ in self._pb_body.ListFields()
        }
        fields_to_hash = present_fields.intersection(fields)
        FieldMask(paths=fields_to_hash).MergeMessage(self._pb_body, masked_d)

        return blake2b(
            masked_d.SerializePartialToString(), digest_size=_DIGEST_SIZE
        ).hexdigest()

    def dump_content_to_datauri(self: T) -> T:
        """Convert :attr:`.content` in :attr:`.uri` inplace with best effort

        :return: itself after processed
        """
        if self.text:
            self.convert_text_to_uri()
        elif self.buffer:
            self.convert_buffer_to_uri()
        elif self.content_type:
            raise NotImplementedError
        return self

    convert_content_to_uri = deprecate_by(dump_content_to_datauri)
