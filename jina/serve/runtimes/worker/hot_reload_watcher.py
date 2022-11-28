import os
import time
import inspect


def hot_reload_watch(executor, py_modules):
    print(f' Hot_reload watch')
    list_of_files_to_monitor = [inspect.getfile(inspect.getmodule(executor))]
    prev_moddates = [os.stat(file) for file in list_of_files_to_monitor]
    while True:
        for i, file in enumerate(list_of_files_to_monitor):
            if prev_moddates[i] != os.stat(file):
                print(f' Lets reload the module of this file {file}')
                module = inspect.getmodule(None, _filename=file)

        time.sleep(10)
