#!/usr/bin/python3

import json
import os
import sys

from packaging import version


def main():
    merged_list = []

    try:
        input_dir = sys.argv[1]
    except IndexError:
        input_dir = 'output'

    try:
        output_file = sys.argv[2]
    except IndexError:
        output_file = 'stats.json'

    for file in os.listdir(input_dir):
        if file.endswith('.json') and file != output_file:
            with open(os.path.join(input_dir, file), 'r') as fp:
                d = json.load(fp)
                for i in d:
                    merged_list.append(i)

    merged_list.sort(key=lambda x: version.Version(x['version']))
    with open(os.path.join(input_dir, output_file), 'w') as fp:
        json.dump(merged_list, fp, indent=2)


if __name__ == '__main__':
    main()
