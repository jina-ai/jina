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
    flow_original = Image.open(os.path.join(cur_dir, 'flow_original.jpg'))
    flow_created = Image.open(os.path.join(cur_dir, 'flow.jpg'))
    assert flow_original.size == flow_created.size
    np.testing.assert_array_almost_equal(flow_original, flow_created)
