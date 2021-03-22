from . import Request


class ReconnectPodRequest(Request):

    @property
    def pod_and_out_port(self) :
        return self.body.pod_and_out_port
