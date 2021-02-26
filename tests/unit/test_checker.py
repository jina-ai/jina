import argparse
import os

from jina.checker import ImportChecker


def test_importchecker(tmpdir):
    args = argparse.Namespace()
    args.cli = 'check'
    tmp_exec_file = os.path.join(str(tmpdir), 'tmp_exec.yml')
    tmp_exec_driver = os.path.join(str(tmpdir), 'tmp_driver.yml')
    args.summary_exec = tmp_exec_file
    args.summary_driver = tmp_exec_driver
    ImportChecker(args)
