#!/usr/bin/env bash
set -ex
if [[ $1 == "windows" ]]; then
    declare -a array2=( $(ls -d tests/{unit}/*/ | grep -v '__pycache__'| grep -v 'unit/serve' | grep -v 'unit/orchestrate'))
    declare -a array3=( $(ls -d tests/{unit}/orchestrate/*/ | grep -v '__pycache__'))
    declare -a array4=( $(ls -d tests/{unit}/serve/*/ | grep -v '__pycache__'))
    dest1=( "${array2[@]}" "${array3[@]}" "${array4[@]}" )
    printf '%s\n' "${dest1[@]}" | jq -R . | jq -cs .
else
    declare -a array1=( "tests/unit/*.py" "tests/integration/*.py")
    declare -a array2=( $(ls -d tests/{unit,integration}/*/ | grep -v '__pycache__' | grep -v 'unit/serve' | grep -v 'unit/orchestrate'))
    declare -a array3=( $(ls -d tests/unit/orchestrate/*/ | grep -v '__pycache__'))
    declare -a array4=( $(ls -d tests/unit/serve/*/ | grep -v '__pycache__'))
    dest=( "${array1[@]}" "${array2[@]}" "${array3[@]}" "${array4[@]}" )

    printf '%s\n' "${dest[@]}" | jq -R . | jq -cs .
fi