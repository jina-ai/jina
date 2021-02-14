from ..drivers import BaseRecursiveDriver

if False:
    from ..types.sets import DocumentSet


class ConvertDriver(BaseRecursiveDriver):
    """Drivers that make sure that specific conversions are applied to the documents.

    .. note::
        The list of functions that can be applied can be found in `:class:`Document`
     """

    def __init__(self, convert_fn: str, *args, **kwargs):
        """
        :param convert_fn: the method name from `:class:`Document` to be applied
        :param *args:
        :param **kwargs: the set of named arguments to be passed to the method with name `convert_fn`
        """
        super().__init__(*args, **kwargs)
        self._convert_fn = convert_fn
        self._convert_fn_kwargs = kwargs

    def _apply_all(
            self,
            docs: 'DocumentSet',
            *args,
            **kwargs,
    ) -> None:
        for d in docs:
            getattr(d, self._convert_fn)(**self._convert_fn_kwargs)


class URI2Buffer(ConvertDriver):
    """Class of `URI2Buffer` driver."""
    def __init__(self, convert_fn: str = 'convert_uri_to_buffer', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)


class URI2DataURI(ConvertDriver):
    """Class of `URI2DataURI` driver."""
    def __init__(self, convert_fn: str = 'convert_uri_to_data_uri', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)


class Buffer2URI(ConvertDriver):
    """Class of `Buffer2URI` driver."""
    def __init__(self, convert_fn: str = 'convert_buffer_to_uri', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)


class BufferImage2Blob(ConvertDriver):
    """Class of `BufferImage2Blob` driver."""
    def __init__(self, convert_fn: str = 'convert_buffer_image_to_blob', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)


class URI2Blob(ConvertDriver):
    """Class of `URI2Blob` driver."""
    def __init__(self, convert_fn: str = 'convert_uri_to_blob', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)


class Text2URI(ConvertDriver):
    """Class of `Text2URI` driver."""
    def __init__(self, convert_fn: str = 'convert_text_to_uri', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)


class URI2Text(ConvertDriver):
    """Class of `URI2Text` driver."""
    def __init__(self, convert_fn: str = 'convert_uri_to_text', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)


class Blob2PngURI(ConvertDriver):
    """Class of `Blob2PngURI` driver."""
    def __init__(self, convert_fn: str = 'convert_blob_to_uri', *args, **kwargs):
        """Set constructor method."""
        super().__init__(convert_fn, *args, **kwargs)
