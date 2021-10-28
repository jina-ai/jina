import multiprocessing
import threading
import time

from jina import Flow


def test_closing_blocked_flow_from_another_thread_via_flow():
    def close_blocked_f(flow):
        time.sleep(3)
        flow.close()

    f = Flow().add()
    with f:
        t = threading.Thread(target=close_blocked_f, args=(f,))
        t.start()
        f.block()


def test_closing_blocked_flow_from_another_thread_via_event():
    ev = threading.Event()

    def close_blocked_f():
        time.sleep(3)
        ev.set()

    f = Flow().add()
    with f:
        t = threading.Thread(target=close_blocked_f)
        t.start()
        f.block(stop_event=ev)


def test_closing_blocked_flow_from_another_process_via_event():
    ev = multiprocessing.Event()

    def close_blocked_f():
        time.sleep(3)
        ev.set()

    f = Flow().add()
    with f:
        t = multiprocessing.Process(target=close_blocked_f)
        t.start()
        f.block(stop_event=ev)
