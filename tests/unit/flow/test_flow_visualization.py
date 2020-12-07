from pathlib import Path

from jina.flow import Flow

cur_dir = Path(__file__).parent


def test_visualization_with_yml_file_img(tmpdir):
    output_file = Path(tmpdir) / 'flow.svg'
    Flow.load_config(str(cur_dir.parent / 'yaml' / 'test_flow_visualization.yml')).plot(
        output=str(output_file))
    assert output_file.exists()


def test_visualization_with_yml_file_jpg(tmpdir):
    output_file = Path(tmpdir) / 'flow.jpg'
    Flow.load_config(str(cur_dir.parent / 'yaml' / 'test_flow_visualization.yml')).plot(
        output=str(output_file))
    assert output_file.exists()


def test_visualization_with_yml_file_jpg_lr(tmpdir):
    output_file = Path(tmpdir) / 'flow-hor.jpg'
    Flow.load_config(str(cur_dir.parent / 'yaml' / 'test_flow_visualization.yml')).plot(
        output=str(output_file),
        vertical_layout=False)
    assert output_file.exists()


def test_visualization_plot_twice(tmpdir):
    output_file1 = Path(tmpdir) / 'flow1.svg'
    output_file2 = Path(tmpdir) / 'flow2.svg'
    (Flow().add(name='pod_a')
     .plot(output=str(output_file1))
     .add(name='pod_b', needs='gateway')
     .join(needs=['pod_a', 'pod_b']).plot(output=str(output_file2)))

    assert output_file1.exists()
    assert output_file2.exists()


def test_visualization_plot_in_middle(tmpdir):
    output_file = Path(tmpdir) / 'flow3.svg'
    (Flow().add(name='pod_a')
     .plot(output=str(output_file))
     .add(name='pod_b', needs='gateway')
     .join(needs=['pod_a', 'pod_b']))

    assert output_file.exists()


def test_flow_before_after_plot(tmpdir):
    output_file = Path(tmpdir) / 'flow.svg'
    Flow().add(uses_before='_pass', uses_after='_pass', name='p1').plot(str(output_file))
    assert output_file.exists()


def test_flow_before_plot(tmpdir):
    output_file = Path(tmpdir) / 'flow.svg'
    Flow().add(uses_before='_pass', name='p1').plot(str(output_file))
    assert output_file.exists()


def test_flow_after_plot(tmpdir):
    output_file = Path(tmpdir) / 'flow.svg'
    Flow().add(uses_after='_pass', name='p1').plot(str(output_file))
    assert output_file.exists()
