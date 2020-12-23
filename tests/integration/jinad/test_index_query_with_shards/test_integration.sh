#!/bin/bash
set -e

if [ "${PWD##*/}" != "jina" ]
  then
    echo "test_integration.sh should only be run from the jina base directory"
    exit 1
fi

docker-compose -f tests/integration/jinad/test_index_query_with_shards/docker-compose.yml --project-directory . up  --build -d

sleep 10
#Indexing part
FLOW_ID=$(curl -s --request PUT "http://localhost:8000/v1/flow/yaml" \
    -H  "accept: application/json" \
    -H  "Content-Type: multipart/form-data" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/index.yml" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/encode.yml" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/slice.yml" \
    -F "pymodules_files=@tests/integration/jinad/test_index_query_with_shards/pods/dummy-encoder.py" \
    -F "yamlspec=@tests/integration/jinad/test_index_query_with_shards/flow.yml"\
    | jq -r .flow_id)
echo "Successfully started the flow: ${FLOW_ID}. Let's index some data"

for i in {1..100};
  do
    TEXT_INDEXED=$(curl -s --request POST -d '{"top_k": 10, "data": ["text:hey, dude message '$(echo $i)'"]}' -H 'Content-Type: application/json' '0.0.0.0:45678/api/index' | \
    jq -e ".index.docs[] | .text")
    echo "Indexed document has the text: ${TEXT_INDEXED}"
  done

curl -s --request GET "http://0.0.0.0:8000/v1/flow/${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"
curl -s --request DELETE "http://0.0.0.0:8000/v1/flow?flow_id=${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"

#Query part
FLOW_ID=$(curl -s --request PUT "http://localhost:8000/v1/flow/yaml" \
    -H  "accept: application/json" \
    -H  "Content-Type: multipart/form-data" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/index.yml" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/encode.yml" \
    -F "uses_files=@tests/integration/jinad/test_index_query_with_shards/pods/slice.yml" \
    -F "pymodules_files=@tests/integration/jinad/test_index_query_with_shards/pods/dummy-encoder.py" \
    -F "yamlspec=@tests/integration/jinad/test_index_query_with_shards/flow.yml"\
    | jq -r .flow_id)
echo "Successfully started the flow: ${FLOW_ID}. Let's send some query"

TEXT_MATCHED=$(curl -s --request POST -d '{"top_k": 10, "data": ["text:anything will match the same"]}' -H 'Content-Type: application/json' '0.0.0.0:45678/api/search' | \
    jq -e ".search.docs[] | .matches[] | .text")

echo -e "documents matched: \n${TEXT_MATCHED}"

echo "$TEXT_MATCHED" >> count.txt
COUNT=$(cat count.txt | wc -l)
rm count.txt

echo "found ${COUNT} matches"

curl -s --request GET "http://0.0.0.0:8000/v1/flow/${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"
curl -s --request DELETE "http://0.0.0.0:8000/v1/flow?flow_id=${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"

docker-compose -f tests/integration/jinad/test_index_query/docker-compose.yml --project-directory . down

if [ $COUNT = 10 ]; then
        echo "Success"
else
        echo -e "Expected top_k to be 10. But got ${COUNT}. Fail"
        exit 1
fi
