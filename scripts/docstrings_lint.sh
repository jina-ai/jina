#!/bin/bash
# required in order to get the status of all the files at once
pip install darglint==1.6.0
pip install pydocstyle==5.1.1
echo ====================================================================================
echo DOCSTRINGS LINT: checking $CHANGED_FILES
echo ------------------------------------------------------------------------------------
echo 'removing files under /tests...'
arrVar=()
# we ignore tests files
for changed_file in $CHANGED_FILES; do
  if [[ ${changed_file} != tests/* ]]; then
    echo keeping ${changed_file}
    arrVar+=(${changed_file})
  fi
done

# if array is empty
if [ ${#arrVar[@]} -eq 0 ]; then
  echo 'nothing to check'
  exit 0
fi

DARGLINT_OUTPUT=$(darglint -v 2 -s sphinx "${arrVar[@]}"); PYDOCSTYLE_OUTPUT=$(pydocstyle --select=D101,D102,D103 "${arrVar[@]}")
# status captured here
if [[ -z "$PYDOCSTYLE_OUTPUT" ]] && [[ -z "$DARGLINT_OUTPUT" ]]; then
  echo 'OK'
  exit 0
else
  echo 'failure. make sure to check the guide for docstrings: https://docs.jina.ai/chapters/docstring.html'
  echo $DARGLINT_OUTPUT
  echo $PYDOCSTYLE_OUTPUT
  exit 1
fi
echo ====================================================================================
