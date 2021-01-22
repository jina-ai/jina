from ..drivers import BaseRecursiveDriver

if False:
    from ..types.sets import DocumentSet


class ConvertDriver(BaseRecursiveDriver):
    def __init__(self, convert_fn: str, *args, **kwargs):
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
    def __init__(self, convert_fn: str = 'convert_uri_to_buffer', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class URI2DataURI(ConvertDriver):
    def __init__(self, convert_fn: str = 'convert_uri_to_data_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class Buffer2URI(ConvertDriver):
    def __init__(self, convert_fn: str = 'convert_buffer_to_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class Text2URI(ConvertDriver):
    def __init__(self, convert_fn: str = 'convert_text_to_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class URI2Text(ConvertDriver):
    def __init__(self, convert_fn: str = 'convert_uri_to_text', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)


class Blob2PngURI(ConvertDriver):
    def __init__(self, convert_fn: str = 'convert_blob_to_uri', *args, **kwargs):
        super().__init__(convert_fn, *args, **kwargs)
