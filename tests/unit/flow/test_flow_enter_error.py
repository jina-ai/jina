import os
import pytest

from jina import Flow

from jina.enums import FlowBuildLevel


class FlowStartupException(Exception):
    pass


class BrokenFlow(Flow):
    def start(self):
        """Start to run all Pods in this Flow.

        Remember to close the Flow with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited all the way from :class:`jina.peapods.peas.BasePea`


        .. # noqa: DAR401

        :return: this instance
        """

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            self.build(copy_flow=False)

        # set env only before the Pod get started
        if self.args.env:
            for k, v in self.args.env.items():
                os.environ[k] = str(v)

        for k, v in self:
            v.args.noblock_on_start = True
            self.enter_context(v)

        for k, v in self:
            try:
                v.wait_start_success()
            except Exception as ex:
                self.logger.error(
                    f'{k}:{v!r} can not be started due to {ex!r}, Flow is aborted'
                )
                self.close()
                raise

        raise FlowStartupException


class WrapContextManager:
    def __init__(self, flow):
        self._flow = flow

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        num_pods = len(self._flow._pod_nodes)
        self._flow.__exit__(exc_type, exc_val, exc_tb)
        assert len(self._flow._pod_nodes) == 0
        assert num_pods == 0


def test_broken_flow_not_hanging():
    """
    This test is crucial for guaranteeing the healthiness of our CI system.
    """
    f = BrokenFlow()

    with WrapContextManager(f):
        with pytest.raises(FlowStartupException):
            with f:
                pass
