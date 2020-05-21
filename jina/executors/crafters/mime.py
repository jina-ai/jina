import mimetypes

from . import BaseDocCrafter


class DataURICrafter(BaseDocCrafter):
    def __init__(self, mimetype: str = None, file_ext: str = None, charset: str = 'utf-8', base64: bool = False, *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.mimetype = None
        if mimetype:
            if mimetype in mimetypes.types_map.values():
                self.mimetype = mimetype
        if file_ext:
            self.mimetype = mimetypes.guess_type(f'*.{file_ext}')[0]

        if not self.mimetype:
            raise NotImplementedError(f'i can not determine the MIME type from '
                                      f'mimetype={mimetype} or file_ext={file_ext}, please check your input')

        self.charset = charset
        self.base64 = base64

    def craft(self, raw_bytes, *args, **kwargs):
        parts = ['data:', self.mimetype]
        if self.charset is not None:
            parts.extend([';charset=', self.charset])
        if self.base64:
            from base64 import encodebytes as encode64
            encoded_data = encode64(raw_bytes).decode(self.charset).strip()
        else:
            from urllib.parse import quote_from_bytes
            encoded_data = quote_from_bytes(raw_bytes)
        parts.extend([',', encoded_data])
        return dict(data_uri=''.join(parts))
