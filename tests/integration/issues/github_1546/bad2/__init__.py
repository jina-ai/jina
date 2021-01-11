from .helper import helper_function

from jina.executors.crafters import BaseCrafter


class CustomCrafter2(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(helper_function)
