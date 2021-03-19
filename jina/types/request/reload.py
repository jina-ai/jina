from . import Request


class ReloadRequest(Request):
    @property
    def path(self):
        return self.body.path

    @path.setter
    def path(self, value):
        self.body.path = value
