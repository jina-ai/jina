import os
import numpy as np
from PIL import Image
from jina.flow import Flow


def test_visualization_URL():
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    flow = (Flow().add(name='pod_a')
            .add(name='pod_b', needs='gateway')
            .join(needs=['pod_a', 'pod_b']))
    url = flow.plot()
    expected_text = 'https://mermaidjs.github.io/mermaid-live-editor/#/view/Z3JhcGggVEQKZ2F0ZXdheVtnYXRld2F5XSAtLT4gcG9kX2FbcG9kX2FdCmdhdGV3YXlbZ2F0ZXdheV0gLS0+IHBvZF9iW3BvZF9iXQpwb2RfYVtwb2RfYV0gLS0+IGpvaW5lcltqb2luZXJdCnBvZF9iW3BvZF9iXSAtLT4gam9pbmVyW2pvaW5lcl0='

    assert expected_text == url


def test_visualization_with_yml_file_img():
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    flow = Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(output='flow_test.jpg')

    with Image.open(os.path.join(cur_dir, 'flow_original_test.jpg')) as flow_original:
        with Image.open(os.path.join(cur_dir, 'flow_test.jpg')) as flow_created:
            assert flow_original.size == flow_created.size
            np.testing.assert_array_almost_equal(flow_original, flow_created)

    os.remove('flow_test.jpg')
