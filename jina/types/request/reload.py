from . import Request


class ReloadRequest(Request):
    @property
    def path(self):
        return self.body.path

    @path.setter
    def path(self, value):
        self.body.path = value

    @property
    def workspace(self):
        return self.body.workspace

    @workspace.setter
    def workspace(self, value):
        self.body.workspace = value
