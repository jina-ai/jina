#!/bin/bash
pip install black==20.8b1
arrVar=()
echo we ignore non-*.py files and files generated from protobuf
excluded_files=(
   jina/proto/jina_pb2.py
   jina/proto/jina_pb2_grpc.py
   docs/conf.py
)
for changed_file in $CHANGED_FILES; do
  if [[ ${changed_file} == *.py ]] && ! [[ " ${excluded_files[@]} " =~ " ${changed_file} " ]]; then
    echo checking ${changed_file}
    arrVar+=(${changed_file})
  fi
done
black -S --check "${arrVar[@]}"
