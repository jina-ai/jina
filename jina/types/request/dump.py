from . import Request


# TODO make Dump a control request to be passed to the Pod directly
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

    @property
    def formats(self):
        """


        .. # noqa: DAR102


        .. # noqa: DAR201
        """
        return self.body.formats

    @formats.setter
    def formats(self, value):
        for v in value:
            self.body.formats.append(v)
