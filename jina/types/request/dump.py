from . import Request


class DumpRequest(Request):
    @property
    def path(self):
        return self.body.path

    @path.setter
    def path(self, value):
        self.body.path = value

    @property
    def shards(self):
        return self.body.shards

    @shards.setter
    def shards(self, value):
        self.body.shards = value

    @property
    def formats(self):
        return self.body.formats

    @formats.setter
    def formats(self, value):
        for v in value:
            self.body.formats.append(v)
