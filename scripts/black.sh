#!/bin/bash
pip install black==20.8b1
arrVar=()
echo we ignore non-*.py files
for changed_file in $CHANGED_FILES; do
  if [[ ${changed_file} == *.py ]]; then
    echo checking ${changed_file}
    arrVar+=(${changed_file})
  fi
done
black -S --check "${arrVar[@]}"
