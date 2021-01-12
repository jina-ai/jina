__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from jina.executors.crafters import BaseCrafter


class DummyCrafter(BaseCrafter):
    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

    def craft(self, text, *args, **kwargs):
        return {'text': text}
