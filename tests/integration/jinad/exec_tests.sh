#!/bin/bash
##############################################################################
#
# @file exec_tests.sh
#
# This bash is intended to be used to execute all the tests for jinad.
# It runs every `test*.sh` script under `tests/integration/jinad` subfolders
# and checks that none of them failed. And also prints the status of the tests
# that passed and which not.
#
# If one test did not pass, it reports a failure and github action will fail
#
##############################################################################

if [ "${PWD##*/}" != "jina" ]
  then
    echo "exec_tests.sh should only be run from the jina base directory"
    exit 1
fi

SKIP_TESTS_SCRIPTS=('./tests/integration/jinad/test_simple_hub_pods/test_integration.sh')
LIST_TEST_SCRIPTS=( $(find "./tests/integration/jinad/" -name "test*sh") )

echo "Have detected ${#LIST_TEST_SCRIPTS[@]} the following tests scripts to run: ${LIST_TEST_SCRIPTS}"

FAILED_TESTS=()
for script in "${LIST_TEST_SCRIPTS[@]}";
  do
    skip=false
    for skip_test_script in "${SKIP_TESTS_SCRIPTS[@]}";
      do
        if [ "$skip_test_script" == "$script" ]; then
          skip=true
        fi
      done

    if [ ${skip} == false ]; then
      echo "Executing test with ${script}\n"
      eval ${script}
      status=$?
      echo "Status ${status}"
      if [ $status -eq 0 ]; then
        echo "${script} test successfully finished\n"
      else
        echo "${script} test failed\n"
        FAILED_TESTS+=(${script})
      fi
    else
      echo "Skipping ${script} test execution"
    fi
  done


NUMBER_FAILED_TESTS=${#FAILED_TESTS[@]}

if [ "${NUMBER_FAILED_TESTS}" = 0 ]; then
  echo "Success"
else
  echo "Detected ${NUMBER_FAILED_TESTS} failed tests. Failed tests summary: \n"
    for failed in "${FAILED_TESTS[@]}";
      do
        echo "${failed} run failed"
      done
      exit 1
fi
