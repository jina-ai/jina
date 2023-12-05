import ctypes
import sys

# local trace function which returns itself
def my_tracer(frame, event, arg = None):
    # extracts frame code
    code = frame.f_code

    # extracts calling function name
    func_name = code.co_name

    # extracts the line number
    line_no = frame.f_lineno

    print(f"A {event} encountered in {func_name}() at line number {line_no} ")

    return my_tracer

sys.settrace(my_tracer)
a = 0
b = a
ctypes.string_at(0)
