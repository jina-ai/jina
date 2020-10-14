__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import atexit
import multiprocessing

__sse_queue__ = multiprocessing.Queue()  #: the global sse log queue
__profile_queue__ = multiprocessing.Queue()  #: the global profile log queue
__log_queue__ = multiprocessing.Queue()  #: the global log queue


def clear_queues():
    """Clear the log queue and profile queue when the program exit

    This is only used when server-side event (SSE) logging is turned on.
    """
    try:
        while not __sse_queue__.empty():
            __sse_queue__.get_nowait()

        while not __profile_queue__.empty():
            __profile_queue__.get_nowait()

        while not __log_queue__.empty():
            __log_queue__.get_nowait()
    except:
        # let's ignore this for a peaceful ending
        pass


atexit.register(clear_queues)  #: clear the log queue when exit
