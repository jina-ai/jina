from . import BaseDriver


class MergeDriver(BaseDriver):
    """Merge the routes information from multiple envelopes into one """

    def __call__(self, *args, **kwargs):
        # take unique routes by service identity
        routes = {(r.pod + r.pod_id): r for m in self.prev_msgs for r in m.envelope.routes}
        self.msg.envelope.ClearField('routes')
        self.msg.envelope.routes.extend(
            sorted(routes.values(), key=lambda x: (x.start_time.seconds, x.start_time.nanos)))
