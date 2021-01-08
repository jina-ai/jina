#!/usr/bin/env bash

set -ex

declare -a array1=( "unit/*.py" "integration/*.py" )
declare -a array2=( $(ls -d tests/{unit,integration}/*/ | cut -f2,3 -d'/' | grep -v '__pycache__' ))
dest=( "${array1[@]}" "${array2[@]}" )
printf '%s\n' "${dest[@]}" | jq -R . | jq -cs .