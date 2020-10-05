import os
import numpy as np
from PIL import Image
from jina.flow import Flow


def test_visualization_url():
    flow = (Flow().add(name='pod_a')
            .add(name='pod_b', needs='gateway')
            .join(needs=['pod_a', 'pod_b']).plot())

    url_split = flow._url.split('view/') #check that has info after standard URL text

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


def test_visualization_plot_twice(tmpdir):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    tmpfile_middle = os.path.join(tmpdir, 'flow_test_middle.jpg')
    tmpfile_end = os.path.join(tmpdir, 'flow_test_end.jpg')

    flow = (Flow().add(name='pod_a')
            .plot(output=tmpfile_middle)
            .add(name='pod_b', needs='gateway')
            .join(needs=['pod_a', 'pod_b']).plot(output=tmpfile_end))

    with Image.open(os.path.join(cur_dir, 'flow_original_middle.jpg')) as flow_original_middle:
        with Image.open(tmpfile_middle) as flow_created_middle:
            assert flow_original_middle.size == flow_created_middle.size
            np.testing.assert_array_almost_equal(flow_original_middle, flow_created_middle)

    with Image.open(os.path.join(cur_dir, 'flow_original_end.jpg')) as flow_original_end:
        with Image.open(tmpfile_end) as flow_created_end:
            assert flow_original_end.size == flow_created_end.size
            np.testing.assert_array_almost_equal(flow_original_end, flow_created_end)