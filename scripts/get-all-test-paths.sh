#!/usr/bin/env bash
set -ex
if [[ $1 == "windows" ]]; then
    declare -a unit_base=( $(ls -d tests/{unit}/*/ | grep -v '__pycache__'| grep -v 'unit/serve' | grep -v 'unit/orchestrate'))
    declare -a unit_orchestrate_flow=( $(ls -d tests/unit/orchestrate/flow/*/ | grep -v '__pycache__'))
    declare -a unit_orchestrate=( $(ls -d tests/unit/orchestrate/*/ | grep -v '__pycache__' | grep -v 'orchestrate/flow'))
    declare -a unit_serve=( $(ls -d tests/{unit}/serve/*/ | grep -v '__pycache__'))
    dest1=( "${unit_base[@]}" "${unit_orchestrate_flow[@]}" "${unit_orchestrate[@]}" "${unit_serve[@]}" )
    printf '%s\n' "${dest1[@]}" | jq -R . | jq -cs .
else
    declare -a unit_integration_base=( "tests/unit/*.py" "tests/integration/*.py")
    declare -a unit_integration_base_2=( $(ls -d tests/{unit,integration}/*/ | grep -v '__pycache__' | grep -v 'unit/serve' | grep -v 'unit/orchestrate'))
    declare -a orchestrate_flow=( $(ls -d tests/unit/orchestrate/flow/*/ | grep -v '__pycache__'))
    declare -a orchestrate_base=( $(ls -d tests/unit/orchestrate/*/ | grep -v '__pycache__' | grep -v 'orchestrate/flow'))
    declare -a unit_serve=( $(ls -d tests/unit/serve/*/ | grep -v '__pycache__'))
    dest=( "${unit_integration_base[@]}" "${unit_integration_base_2[@]}" "${orchestrate_flow[@]}" "${orchestrate_base[@]}" "${unit_serve[@]}" )

    printf '%s\n' "${dest[@]}" | jq -R . | jq -cs .
fi