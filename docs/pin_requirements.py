import re
import sys

file_name = sys.argv[1]
with open(file_name, 'r') as f:
    input = f.read()


# official semver regex: https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
versions_regex = '(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)'

output = re.sub(
    f'(?P<dep>[a-zA-Z0-9]+)(==|>=)(?P<version>{versions_regex}).*:',
    r'\g<dep>==\g<version>:',
    input,
)


with open(file_name, 'w') as f:
    f.write(output)
