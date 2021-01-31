from . import Request


class DeleteRequest(Request):

    @property
    def ids(self):
        return self.body.ids
