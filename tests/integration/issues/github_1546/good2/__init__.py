from .helper import helper_function

from jina.executors.crafters import BaseSegmenter


class CustomCrafter4(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(helper_function)
