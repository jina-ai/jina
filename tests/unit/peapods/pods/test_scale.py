import pytest

from jina.peapods.pods import Pod
from jina.parsers import set_pod_parser
from jina.excepts import RuntimeFailToStart, ScalingFails


@pytest.mark.asyncio
async def test_scale_given_replicas_greater_than_num_peas_success():
    # trigger scale up and success
    args = set_pod_parser().parse_args(['--replicas', '3', '--name', 'test'])
    with Pod(args) as p:
        assert len(p.peas_args['peas']) == 3
        await p.scale(replicas=5)
        assert p.replica_set.num_peas == 5
        assert len(p.peas_args['peas']) == 5


@pytest.mark.asyncio
@pytest.mark.timeout(2)
async def test_scale_given_replicas_greater_than_num_peas_fail(mocker):
    # trigger scale up and fail
    args = set_pod_parser().parse_args(['--replicas', '3', '--name', 'test'])
    mocker.patch(
        'jina.peapods.peas.BasePea.async_wait_start_success',
        side_effect=RuntimeFailToStart,
    )
    with Pod(args) as p:
        with pytest.raises(ScalingFails):
            await p.scale(replicas=5)


@pytest.mark.asyncio
async def test_scale_given_replicas_equal_to_num_peas():
    # trigger scale up and success
    args = set_pod_parser().parse_args(['--replicas', '3', '--name', 'test'])
    with Pod(args) as p:
        assert len(p.peas_args['peas']) == 3
        await p.scale(replicas=3)
        assert p.replica_set.num_peas == 3
        assert len(p.peas_args['peas']) == 3


@pytest.mark.asyncio
async def test_scale_given_replicas_less_than_num_peas_success():
    # trigger scale up and success
    args = set_pod_parser().parse_args(['--replicas', '3', '--name', 'test'])
    with Pod(args) as p:
        assert len(p.peas_args['peas']) == 3
        await p.scale(replicas=1)
        assert p.replica_set.num_peas == 1
        assert len(p.peas_args['peas']) == 1
