from . import Request


class ReloadFromTrainingRequest(Request):
    @property
    def path(self):
        return self.body.path

    @path.setter
    def path(self, value):
        self.body.path = value
