import os

from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_visualization_with_yml_file_img():
    Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(output='flow.svg')
    assert os.path.exists('flow.svg')


def test_visualization_with_yml_file_jpg():
    Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(output='flow.jpg',
                                                                                        image_type='jpg')
    assert os.path.exists('flow.jpg')

def test_visualization_with_yml_file_jpg_lr():
    Flow.load_config(os.path.join(cur_dir, '../yaml/test_flow_visualization.yml')).plot(output='flow-hor.jpg',
                                                                                        image_type='jpg',
                                                                                        vertical_layout=False)
    assert os.path.exists('flow-hor.jpg')

def test_visualization_plot_twice():
    (Flow().add(name='pod_a')
     .plot(output='flow1.svg')
     .add(name='pod_b', needs='gateway')
     .join(needs=['pod_a', 'pod_b']).plot(output='flow2.svg'))

    assert os.path.exists('flow1.svg')
    assert os.path.exists('flow2.svg')


def test_visualization_plot_in_middle():
    (Flow().add(name='pod_a')
     .plot(output='flow3.svg')
     .add(name='pod_b', needs='gateway')
     .join(needs=['pod_a', 'pod_b']))

    assert os.path.exists('flow3.svg')
