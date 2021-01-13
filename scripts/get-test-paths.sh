#!/usr/bin/env bash

set -ex

declare -a array1=( "${1}/unit/*.py" "${1}/integration/*.py" "${1}/distributed/*.py")
declare -a array2=( $(ls -d ${1}/{unit,integration,distributed}/*/ | grep -v '__pycache__' ))
dest=( "${array1[@]}" "${array2[@]}" )
printf '%s\n' "${dest[@]}" | jq -R . | jq -cs .