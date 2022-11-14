from jina import Flow

namespace = 'meow'
dump_path = './k8s_flow'
flow = Flow(
    name=namespace,
    tracing=True,
    traces_exporter_host='otel-collector',
    traces_exporter_port=4317,
    metrics=True,
    metrics_exporter_host='otel-collector',
    metrics_exporter_port=4317,
    ).add(
    name='segmenter',
    uses='docker://test-executor'
)
flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)
