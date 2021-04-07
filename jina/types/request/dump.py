from . import Request


class DumpRequest(Request):
    """A request telling an Indexer to dump its data"""

    @property
    def path(self):
        """


        .. # noqa: DAR102


        .. # noqa: DAR201
        """
        return self.body.path

    @path.setter
    def path(self, value):
        self.body.path = value

    @property
    def shards(self):
        """


        .. # noqa: DAR102


        .. # noqa: DAR201
        """
        return self.body.shards

    @shards.setter
    def shards(self, value):
        self.body.shards = value
