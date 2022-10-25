from typing import List
import argparse
import json

parser = argparse.ArgumentParser(prog="Prepender docs/_versions.json")
parser.add_argument(
    "--version",
    type=str,
    help="The version we wish to prepend (e.g. v0.18.0)",
    required=True,
)
args = parser.parse_args()

with open("./docs/_versions.json") as f:
    versions: List[dict] = json.load(f)
    element = {k: v for k, v in args._get_kwargs()}
    if element != versions[0]:
        versions.insert(0, element)

with open("./docs/_versions.json", "w") as f:
    json.dump(versions, f)
