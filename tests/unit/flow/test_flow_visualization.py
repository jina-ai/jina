from jina.flow import Flow

def test_visualization():
    flow = (Flow().add(name='pod_a')
                    .add(name='pod_b', needs='gateway')
                    .join(needs=['pod_a', 'pod_b']))

    flow.mermaidstr_to_jpg()

