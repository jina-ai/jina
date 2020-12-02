#!/bin/bash
set -e

if [ "${PWD##*/}" != "jina" ]
  then
    echo "test_integration.sh should only be run from the jina base directory"
    exit 1
fi

docker-compose -f tests/integration/jinad/test_index_query_with_shards/docker-compose.yml --project-directory . up  --build -d

sleep 5
#Indexing part
FLOW_ID=$(curl -s --request PUT "http://localhost:8000/v1/flow/yaml" \
    -H  "accept: application/json" \
    -H  "Content-Type: multipart/form-data" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/index.yml" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/encode.yml" \
    -F "pymodules_files=@tests/integration/jinad/test_index_query_with_shards/pods/dummy-encoder.py" \
    -F "yamlspec=@tests/integration/jinad/test_index_query_with_shards/flow.yml"\
    | jq -r .flow_id)
echo "Successfully started the flow: ${FLOW_ID}. Let's index some data"

for i in {1..100};
  do
    TEXT_INDEXED=$(curl --request POST -d '{"top_k": 10, "data": ["text:hey, dude message '$(echo $i)'"]}' -H 'Content-Type: application/json' '0.0.0.0:45678/api/index' | \
    jq -e ".index.docs[] | .text")
    echo "Indexed document has the text: ${TEXT_INDEXED}"
  done

echo "Indexed document has the text: ${TEXT_INDEXED}"
curl --request GET "http://0.0.0.0:8000/v1/flow/${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"
curl --request DELETE "http://0.0.0.0:8000/v1/flow?flow_id=${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"

#Query part
FLOW_ID=$(curl -s --request PUT "http://localhost:8000/v1/flow/yaml" \
    -H  "accept: application/json" \
    -H  "Content-Type: multipart/form-data" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/index.yml" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/encode.yml" \
    -F "pymodules_files=@tests/integration/jinad/test_index_query_with_shards/pods/dummy-encoder.py" \
    -F "yamlspec=@tests/integration/jinad/test_index_query_with_shards/flow.yml"\
    | jq -r .flow_id)
echo "Successfully started the flow: ${FLOW_ID}. Let's send some query"

TEXT_MATCHED=$(curl --request POST -d '{"top_k": 10, "data": ["text:anything will match the same"]}' -H 'Content-Type: application/json' '0.0.0.0:45678/api/search' | \
    jq -e ".search.docs[] | .matches[] | .text")
echo "document matched has the text: ${TEXT_INDEXED}"
curl --request GET "http://0.0.0.0:8000/v1/flow/${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"
curl --request DELETE "http://0.0.0.0:8000/v1/flow?flow_id=${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"

docker-compose -f tests/integration/jinad/test_index_query/docker-compose.yml --project-directory . down

EXPECTED_TEXT='"text:hey, dude"'

if [ "$EXPECTED_TEXT" = "$TEXT_MATCHED" ]; then
        echo "Success"
else
        echo "Fail"
        exit 1
fi
