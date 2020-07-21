from jina.drivers.control import ControlReqDriver


class MyAwesomeDriver(ControlReqDriver):
    def __call__(self, *args, **kwargs):
        print('hello from customized drivers')
        super().__call__(*args, **kwargs)
