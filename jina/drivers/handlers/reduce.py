def merge_routes(exec_fn, pea, req, msg, pre_reqs, prev_msgs):
    """Merge the routes information from multiple envelopes into one """
    # take unique routes by service identity
    routes = {(r.pod + r.pod_id): r for m in prev_msgs for r in m.envelope.routes}
    msg.envelope.ClearField('routes')
    msg.envelope.routes.extend(sorted(routes.values(), key=lambda x: (x.start_time.seconds, x.start_time.nanos)))
