import os
import sys
print(sys.path)
print(sys.modules)
# from jina.parsers import set_pod_parser
# from jina.logging.logger import JinaLogger
# from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler


os.environ['JINA_LOG_LEVEL'] = 'DEBUG'

class A():

    def print(*args):
        print(f' HEY HERE CALLING PRINT OF A')


def function_name():
    return A()


def create_worker_request_handler():

    # args = set_pod_parser().parse_args([])
    # logger = JinaLogger('TEST')
    # logger.warning(f' HEY HERE CREATING')
    # w = WorkerRequestHandler(args, logger)
    # return w
    return A()
