#!/usr/bin/env bash

set -ex

declare -a array1=( "tests/unit/*.py" "tests/integration/*.py" )
declare -a array2=( $(ls -d tests/{unit,integration}/*/ | grep -v '__pycache__' ))
dest1=( "${array1[@]}" "${array2[@]}" )

declare -a array1=( "tests/jinad/unit/*.py" "tests/jinad/integration/*.py" )
declare -a array2=( $(ls -d tests/jinad/{unit,integration}/*/ | grep -v '__pycache__' ))
dest2=( "${array1[@]}" "${array2[@]}" )

dest=( "${dest1[@]}" "${dest2[@]}" )

printf '%s\n' "${dest[@]}" | jq -R . | jq -cs .