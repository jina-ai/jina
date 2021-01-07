from jina.executors.crafters import BaseSegmenter
from .helper import helper_function


class CustomCrafter1(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(helper_function)
