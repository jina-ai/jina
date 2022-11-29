from jina import Flow

flow = Flow().config_gateway(
    port=8501, protocol='http', uses='streamlit_gateway/config.yml'
)
with flow:
    flow.block()
