from jina import Executor
from jinahub.helper import helper_function


class GoodCrafter1(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(helper_function)
