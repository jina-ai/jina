#
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

set -e

if [ "${PWD##*/}" != "jina" ]
  then
    echo "exec_tests.sh should only be run from the jina base directory"
    exit 1
fi

LIST_TEST_SCRIPTS=$(find "./tests/integration/jinad/" -name "test*sh")

echo "Have detected the following tests scripts to run: ${LIST_TEST_SCRIPTS}"

FAILED_TESTS=()
for script in ${LIST_TEST_SCRIPTS};
  do
    echo "Executing test with ${script}"
    exec ${script}
    if [ $? -eq 0 ]; then
      echo "${script} test successfully finished"
    else
      echo "${script} test failed"
      FAILED_TESTS+=(${script})
    fi
  done


NUMBER_FAILED_TESTS=${#FAILED_TESTS[@]}

if [ "${NUMBER_FAILED_TESTS}" = 0 ]; then
        echo "Success"
else
        echo "Failed tests summary:"
        for failed in ${FAILED_TESTS};
          do
            echo "${failed} run failed"
          done
        exit 1
fi
