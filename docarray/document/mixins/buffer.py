from .helper import _uri_to_buffer, _to_datauri
from ...helper import T, deprecate_by


class BufferDataMixin:
    """Provide helper functions for :class:`Document` to handle binary data. """

    def load_uri_to_buffer(self: T) -> T:
        """Convert :attr:`.uri` to :attr:`.buffer` inplace.
        Internally it downloads from the URI and set :attr:`buffer`.

        :return: itself after processed
        """
        self.buffer = _uri_to_buffer(self.uri)
        return self

    def dump_buffer_to_datauri(
        self: T, charset: str = 'utf-8', base64: bool = False
    ) -> T:
        """Convert :attr:`.buffer` to data :attr:`.uri` in place.
        Internally it first reads into buffer and then converts it to data URI.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that
            frequently uses non-US-ASCII characters.

        :return: itself after processed
        """

        if not self.mime_type:
            raise ValueError(
                f'{self.mime_type} is unset, can not convert it to data uri'
            )

        self.uri = _to_datauri(
            self.mime_type, self.buffer, charset, base64, binary=True
        )
        return self

    convert_buffer_to_uri = deprecate_by(dump_buffer_to_datauri)
    convert_uri_to_buffer = deprecate_by(load_uri_to_buffer)
