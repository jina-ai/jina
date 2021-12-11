from typing import Union, BinaryIO

import numpy as np

from ...helper import T, deprecate_by


class VideoDataMixin:
    """Provide helper functions for :class:`Document` to support video data. """

    def load_uri_to_video_blob(self: T, only_keyframes: bool = False) -> T:
        """Convert a :attr:`.uri` to a video ndarray :attr:`.blob`.

        :param only_keyframes: only keep the keyframes in the video
        :return: Document itself after processed
        """
        import av

        with av.open(self.uri) as container:
            if only_keyframes:
                stream = container.streams.video[0]
                stream.codec_context.skip_frame = 'NONKEY'

            frames = []
            for frame in container.decode(video=0):
                img = frame.to_image()
                frames.append(np.asarray(img))

        self.blob = np.moveaxis(np.stack(frames), 1, 2)
        return self

    def dump_video_blob_to_file(
        self: T, file: Union[str, BinaryIO], frame_rate: int = 30, codec: str = 'h264'
    ) -> T:
        """Save :attr:`.blob` as a video mp4/h264 file.

        :param file: The file to open, which can be either a string or a file-like object.
        :param frame_rate: frames per second
        :param codec: the name of a decoder/encoder
        :return: itself after processed
        """
        if (
            self.blob.ndim != 4
            or self.blob.shape[-1] != 3
            or self.blob.dtype != np.uint8
        ):
            raise ValueError(
                f'expects `.blob` with dtype=uint8 and ndim=4 and the last dimension is 3, '
                f'but receiving {self.blob.shape} in {self.blob.dtype}'
            )

        video_blob = np.moveaxis(np.clip(self.blob, 0, 255), 1, 2)

        import av

        with av.open(file, mode='w') as container:
            stream = container.add_stream(codec, rate=frame_rate)
            stream.width = self.blob.shape[1]
            stream.height = self.blob.shape[2]
            stream.pix_fmt = 'yuv420p'

            for b in video_blob:
                frame = av.VideoFrame.from_ndarray(b, format='rgb24')
                for packet in stream.encode(frame):
                    container.mux(packet)

            for packet in stream.encode():
                container.mux(packet)
        return self

    convert_uri_to_video_blob = deprecate_by(load_uri_to_video_blob)
