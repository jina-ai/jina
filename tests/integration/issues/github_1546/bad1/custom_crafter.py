from jina.executors.crafters import BaseCrafter
from .helper import helper_function


class CustomCrafter1(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(helper_function)
