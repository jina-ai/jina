import zipfile
from typing import Iterator, Callable

from .grpc import GrpcClient
from .helper import ProgressBar
from ...logging.profile import TimeContext

if False:
    # fix type-hint complain for sphinx and flake
    import argparse
    from ...proto import jina_pb2


class PyClient(GrpcClient):
    """A simple Python client for connecting to the frontend """

    def __init__(self, args: 'argparse.Namespace', delay: bool = False):
        """

        :param args: args provided by the CLI
        :param delay: if ``True`` then the client starts sending request after initializing, otherwise one needs to set
            the :attr:`raw_bytes` before using :func:`start` or :func:`call`
        """
        super().__init__(args)
        self._raw_bytes = None
        if not delay:
            self._raw_bytes = self._get_raw_bytes_from_args(args)
            self.start()

    @staticmethod
    def _get_raw_bytes_from_args(args):
        if args.txt_file:
            all_bytes = (v.encode() for v in args.txt_file)
        elif args.image_zip_file:
            zipfile_ = zipfile.ZipFile(args.image_zip_file)
            all_bytes = (zipfile_.open(v).read() for v in zipfile_.namelist())
        elif args.video_zip_file:
            zipfile_ = zipfile.ZipFile(args.video_zip_file)
            all_bytes = (zipfile_.open(v).read() for v in zipfile_.namelist())
        else:
            all_bytes = None
        return all_bytes

    def call(self, callback: Callable[['jina_pb2.Message'], None] = None) -> None:
        """ Calling the server, better use :func:`start` instead.

        :param callback: a callback function, invoke after every response is received
        """
        kwargs = vars(self.args)
        kwargs['data'] = self.raw_bytes

        from . import request
        tname = self.args.mode
        req_iter = getattr(request, tname)(**kwargs)

        with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
            for resp in self._stub.Call(req_iter):
                if callback:
                    try:
                        callback(resp)
                    except Exception as ex:
                        self.logger.error('error in callback: %s' % ex, exc_info=True)
                p_bar.update()

    @property
    def raw_bytes(self) -> Iterator[bytes]:
        """ An iterator of bytes, each element represents a document's raw content,
        i.e. ``raw_bytes`` defined int the protobuf
        """
        if self._raw_bytes:
            return self._raw_bytes
        else:
            raise ValueError('raw_bytes is empty or not set')

    @raw_bytes.setter
    def raw_bytes(self, bytes_gen: Iterator[bytes]):
        if self._raw_bytes:
            self.logger.warning('raw_bytes is not empty, overrided')
        self._raw_bytes = bytes_gen
