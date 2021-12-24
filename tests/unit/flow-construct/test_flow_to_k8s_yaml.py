import os

from jina import Flow


def test_flow_to_k8s_yaml(tmpdir):
    f = (
        Flow()
        .add()
        .add(shards=3)
        .add(uses_before='docker://image', uses_after='docker://image')
    )
    f.to_k8s_yaml(output_base_path=os.path.join(str(tmpdir), 'k8s'))
    assert os.listdir(os.path.join(str(tmpdir), 'k8s')) == [
        'gateway',
        'executor2',
        'executor1',
        'executor0',
    ]
    assert os.listdir(os.path.join(str(tmpdir), 'k8s/gateway')) == ['gateway.yml']
    assert sorted(os.listdir(os.path.join(str(tmpdir), 'k8s/executor0'))) == [
        'executor0-head-0.yml',
        'executor0.yml',
    ]
    assert sorted(os.listdir(os.path.join(str(tmpdir), 'k8s/executor1'))) == [
        'executor1-0.yml',
        'executor1-1.yml',
        'executor1-2.yml',
        'executor1-head-0.yml',
    ]
    assert sorted(os.listdir(os.path.join(str(tmpdir), 'k8s/executor2'))) == [
        'executor2-head-0.yml',
        'executor2.yml',
    ]
