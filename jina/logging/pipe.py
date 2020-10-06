__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import re
import sys
import time
from collections import defaultdict

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class PipeLogger:
    def __init__(self, args: 'argparse.Namespace'):
        """ Start a pipe logger to beautify the log

        :param args: the parsed arguments from the CLI
        """
        self.args = args
        self._preserved_logs = defaultdict(str)

    def start(self):
        """ Start to receive logs from pipe"""

        try:
            for l in sys.stdin:
                m = re.match(self.args.groupby_regex, l)
                if m:
                    self._preserved_logs[m.group(0)] = l, time.perf_counter()
                    os.system('cls' if os.name == 'nt' else 'clear')
                    now_time = time.perf_counter()
                    for k, v in sorted(self._preserved_logs.items(), key=lambda x: x[1]):
                        if self.args.refresh_time < 0 or (now_time - v[1]) < self.args.refresh_time:
                            sys.stdout.write(v[0])
                else:
                    sys.stdout.write(l)
        except KeyboardInterrupt:
            pass
