from ..drivers import RecursiveMixin, BaseRecursiveDriver

if False:
    from ..types.sets import DocumentSet


class ConvertDriver(RecursiveMixin, BaseRecursiveDriver):
    """Drivers that make sure that specific conversions are applied to the documents.

    .. note::
        The list of functions that can be applied can be found in `:class:`Document`
     """

    def __init__(self, convert_fn: str, *args, **kwargs):
        """
        :param convert_fn: the method name from `:class:`Document` to be applied
        :param *args: *args for super
        :param **kwargs: the set of named arguments to be passed to `convert_fn`
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
    """Driver to convert URI to buffer"""
    def __init__(self, convert_fn: str = 'convert_uri_to_buffer', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class URI2DataURI(ConvertDriver):
    """Driver to convert URI to data URI
    """
    def __init__(self, convert_fn: str = 'convert_uri_to_data_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class Buffer2URI(ConvertDriver):
    """Driver to convert buffer to URI
    """
    def __init__(self, convert_fn: str = 'convert_buffer_to_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class BufferImage2Blob(ConvertDriver):
    """Driver to convert image buffer to blob
    """
    def __init__(self, convert_fn: str = 'convert_buffer_image_to_blob', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class URI2Blob(ConvertDriver):
    """Driver to convert URI to blob
    """
    def __init__(self, convert_fn: str = 'convert_uri_to_blob', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class Text2URI(ConvertDriver):
    """Driver to convert text to URI
    """
    def __init__(self, convert_fn: str = 'convert_text_to_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class URI2Text(ConvertDriver):
    """Driver to convert URI to text
    """
    def __init__(self, convert_fn: str = 'convert_uri_to_text', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class Blob2PngURI(ConvertDriver):
    """Driver to convert blob to URI
    """
    def __init__(self, convert_fn: str = 'convert_blob_to_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)
