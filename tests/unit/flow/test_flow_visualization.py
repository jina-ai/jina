import os

from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_visualization_with_yml_file_img(tmpdir):
    Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(
        output=os.path.join(tmpdir, 'flow.svg'))
    assert os.path.exists(os.path.join(tmpdir, 'flow.svg'))


def test_visualization_with_yml_file_jpg(tmpdir):
    Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(
        output=os.path.join(tmpdir, 'flow.jpg'))
    assert os.path.exists(os.path.join(tmpdir, 'flow.jpg'))


def test_visualization_with_yml_file_jpg_lr(tmpdir):
    Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(
        output=os.path.join(tmpdir, 'flow-hor.jpg'),
        vertical_layout=False)
    assert os.path.exists(os.path.join(tmpdir, 'flow-hor.jpg'))


def test_visualization_plot_twice(tmpdir):
    (Flow().add(name='pod_a')
     .plot(output=os.path.join(tmpdir, 'flow1.svg'))
     .add(name='pod_b', needs='gateway')
     .join(needs=['pod_a', 'pod_b']).plot(output=os.path.join(tmpdir, 'flow2.svg')))

    assert os.path.exists(os.path.join(tmpdir, 'flow1.svg'))
    assert os.path.exists(os.path.join(tmpdir, 'flow2.svg'))


def test_visualization_plot_in_middle(tmpdir):
    (Flow().add(name='pod_a')
     .plot(output=os.path.join(tmpdir, 'flow3.svg'))
     .add(name='pod_b', needs='gateway')
     .join(needs=['pod_a', 'pod_b']))

    assert os.path.exists(os.path.join(tmpdir, 'flow3.svg'))


def test_flow_before_after_plot(tmpdir):
    Flow().add(uses_before='_pass', uses_after='_pass', name='p1').plot(os.path.join(tmpdir, 'flow.svg'))
    assert os.path.exists(os.path.join(tmpdir, 'flow.svg'))


def test_flow_before_plot(tmpdir):
    Flow().add(uses_before='_pass', name='p1').plot(os.path.join(tmpdir, 'flow.svg'))
    assert os.path.exists(os.path.join(tmpdir, 'flow.svg'))


def test_flow_after_plot(tmpdir):
    Flow().add(uses_after='_pass', name='p1').plot(os.path.join(tmpdir, 'flow.svg'))
    assert os.path.exists(os.path.join(tmpdir, 'flow.svg'))
