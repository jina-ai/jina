import os

import streamlit.web.bootstrap
from streamlit.web.server import Server

from jina import Gateway

cur_dir = os.path.dirname(__file__)


class StreamlitGateway(Gateway):
    def __init__(self, streamlit_script: str = 'app.py', **kwargs):
        super().__init__(**kwargs)
        self.streamlit_script = streamlit_script
        self.server = None

    async def setup_server(self):
        streamlit.web.bootstrap._fix_sys_path(self.streamlit_script)
        streamlit.web.bootstrap._fix_matplotlib_crash()
        streamlit.web.bootstrap._fix_tornado_crash()
        streamlit.web.bootstrap._fix_sys_argv(self.streamlit_script, ())
        streamlit.web.bootstrap._fix_pydeck_mapbox_api_warning()
        streamlit.web.bootstrap._install_pages_watcher(self.streamlit_script)

        self.server = Server(
            os.path.join(cur_dir, self.streamlit_script),
            f'"python -m streamlit" run --browser.serverPort {self.port} {self.streamlit_script}',
        )

    async def run_server(self):
        await self.server.start()
        streamlit.web.bootstrap._on_server_start(self.server)
        streamlit.web.bootstrap._set_up_signal_handler(self.server)
        await self.server.stopped

    async def shutdown(self):
        self.server.stop()
