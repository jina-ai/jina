import asyncio

import streamlit as st
from docarray import Document, DocumentArray

from jina.serve.streamer import GatewayStreamer

streamer = GatewayStreamer.get_streamer()
st.title('Streamlit app running on Jina Gateway')


async def send_docs():
    res = []
    async for docs in streamer.stream_docs(
        docs=DocumentArray.empty(10),
        exec_endpoint='/',
    ):
        for doc in docs:
            res.append(doc.text)
    st.text('results:\n' + '\n'.join(res))


asyncio.run(send_docs())
