import os
import numpy as np

from PIL import Image

from jina.flow import Flow


def test_visualization():
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    flow = (Flow().add(name='pod_a')
            .add(name='pod_b', needs='gateway')
            .join(needs=['pod_a', 'pod_b']))

    flow.mermaidstr_to_jpg()
    with Image.open(os.path.join(cur_dir, 'flow_original.jpg')) as flow_original:
        with Image.open(os.path.join(cur_dir, 'flow.jpg')) as flow_created:
            assert flow_original.size == flow_created.size
            np.testing.assert_array_almost_equal(flow_original, flow_created)
