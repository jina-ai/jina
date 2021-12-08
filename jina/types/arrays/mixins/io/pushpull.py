import io
from contextlib import nullcontext
from typing import Type, TYPE_CHECKING

import requests

from .....helper import get_request_header

if TYPE_CHECKING:
    from .....helper import T


class PushPullMixin:
    """Transmitting :class:`DocumentArray` via Jina Cloud Service"""

    _service_url = 'http://apihubble.staging.jina.ai/v2/rpc/da.'

    def push(self, keyphrase: str) -> None:
        """Push this DocumentArray object to Jina Cloud which can be later retrieved via :meth:`.push`

        :param keyphrase: a key that later can be used for retrieve this :class:`DocumentArray`.
        """
        payload = {'token': keyphrase}

        files = [('file', ('DocumentArray', bytes(self)))]

        requests.post(
            self._service_url + 'push',
            data=payload,
            files=files,
            headers=get_request_header(),
        )

    @classmethod
    def pull(cls: Type['T'], keyphrase: str, show_progress: bool = False) -> 'T':
        """Pulling a :class:`DocumentArray` from Jina Cloud Service to local.

        :param keyphrase: the upload token set during :meth:`.push`
        :param show_progress: if to show a progress bar on pulling
        :return: a :class:`DocumentArray` object
        """

        url = f'{cls._service_url}pull?token={keyphrase}'
        response = requests.get(url)

        if show_progress:
            from rich.progress import (
                BarColumn,
                DownloadColumn,
                Progress,
                TimeRemainingColumn,
                TransferSpeedColumn,
            )

            progress = Progress(
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
                transient=True,
            )
        else:
            progress = nullcontext()

        url = response.json()['data']['download']

        with requests.get(
            url,
            stream=True,
            headers=get_request_header(),
        ) as r, progress:
            r.raise_for_status()
            if show_progress:
                task_id = progress.add_task('download', start=False)
                progress.update(task_id, total=int(r.headers['Content-length']))
            with io.BytesIO() as f:
                chunk_size = 8192
                if show_progress:
                    progress.start_task(task_id)
                for chunk in r.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    if show_progress:
                        progress.update(task_id, advance=len(chunk))

                return cls.load_binary(f.getvalue())
