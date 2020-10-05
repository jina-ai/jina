import os
import numpy as np
from PIL import Image
from jina.flow import Flow


def test_visualization_url():
    flow = (Flow().add(name='pod_a')
            .add(name='pod_b', needs='gateway')
            .join(needs=['pod_a', 'pod_b']).plot())

    url_split = flow._url.split("view/") #check that has info after standard URL text

    assert url_split is not ' '


def test_visualization_with_yml_file_img(tmpdir):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    tmpfile = os.path.join(tmpdir, 'flow_test.jpg')

    flow = Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(output=tmpfile)

    with Image.open(os.path.join(cur_dir, 'flow_test.jpg')) as flow_original:
        with Image.open(tmpfile) as flow_created:
            assert flow_original.size == flow_created.size
            np.testing.assert_array_almost_equal(flow_original, flow_created)


def test_visualization_plot_in_middle(tmpdir):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    tmpfile = os.path.join(tmpdir, 'flow_test_middle.jpg')

    flow = (Flow().add(name='pod_a')
            .plot(output=tmpfile)
            .add(name='pod_b', needs='gateway')
            .join(needs=['pod_a', 'pod_b']))

    with Image.open(os.path.join(cur_dir, 'flow_original_middle.jpg')) as flow_original:
        with Image.open(tmpfile) as flow_created:
            assert flow_original.size == flow_created.size
            np.testing.assert_array_almost_equal(flow_original, flow_created)