#!/usr/bin/env bash

# set -ex

if [[ $1 == "windows" ]]; then
    # declare -a array1=( "tests/system/*.py" )
    declare -a array2=( $(ls -d tests/{unit,system}/*/ | grep -v '__pycache__' ))
    # dest=( "${array1[@]}" "${array2[@]}" )
    printf '%s\n' "${array2[@]}" | jq -R . | jq -cs .
else
    # declare -a array1=( "tests/unit/*.py" "tests/integration/*.py" "tests/distributed/*.py" "tests/system/*.py")
    # declare -a array2=( $(ls -d tests/{unit,integration,distributed,system}/*/ | grep -v '__pycache__' ))
    # dest1=( "${array1[@]}" "${array2[@]}" )

    # declare -a array1=( "tests/daemon/unit/*.py" )
    # declare -a array2=( $(ls -d tests/daemon/{unit,integration}/*/ | grep -v '__pycache__' ))
    # dest2=( "${array1[@]}" "${array2[@]}" )

    # dest=( "${dest1[@]}" "${dest2[@]}" )

    # space separated tests (each will run in separate runner)
    declare -a distributed_tests=("tests/distributed/test_remote_peas/")
    
    # will be executed in one runner
    declare -a comma_separated_tests=("tests/unit/peapods/runtimes/worker","tests/unit/peapods/runtimes/head","tests/unit/peapods/runtimes/request_handlers/","tests/unit/peapods/runtimes/gateway/grpc/test_grpc_gateway_runtime.py","tests/unit/peapods/runtimes/gateway/graph/test_topology_graph.py","tests/unit/peapods/test_networking.py","tests/unit/peapods/pods/test_pods.py","tests/unit/peapods/pods/test_scale.py","tests/unit/peapods/pods/test_pod_factory.py","tests/integration/runtimes/test_runtimes.py","tests/integration/peas/test_pea.py","tests/integration/peas/container/test_pea.py","tests/unit/peapods/peas/container/test_container_pea.py","tests/unit/peapods/peas/test_pea.py")

    dest=( "${distributed_tests[@]}" "${comma_separated_tests[@]}" )

    # IFS=','
    # for current_test in ${comma_separated_tests}; do 
    #     echo "${current_test}"
    # done

    # printf '%s\n' "${dest[@]}" | jq -R . # | jq -cs .
    printf '%s\n' "${dest[@]}" | jq -R . | jq -cs .
fi
