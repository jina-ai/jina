from jina.flow import Flow


flow = (Flow().add(name='pod_a')
                .add(name='pod_b', needs='gateway')
                .join(needs=['pod_a', 'pod_b'], uses='- !ConcatEmbedDriver | {recur_range: [0, 1]}'))

flow.mermaidstr_to_jpg()

