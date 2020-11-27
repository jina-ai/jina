set -e

if [ "${PWD##*/}" != "jina" ]
  then
    echo "test_integration.sh should only be run from the jina base directory"
    exit 1
fi

docker-compose -f tests/integration/jinad/test_simple_distributed_with_shards/docker-compose.yml --project-directory . up  --build -d

sleep 5

FLOW_ID=$(curl -s --request PUT "http://localhost:8000/v1/flow/yaml" \
    -H  "accept: application/json" \
    -H  "Content-Type: multipart/form-data" \
    -F "yamlspec=@tests/integration/jinad/test_simple_distributed_with_shards/flow.yml"\
    | jq -r .flow_id)

echo "Successfully started the flow: ${FLOW_ID}"

TEXT_BACK=$(curl --request POST -d '{"top_k": 10, "data": ["text:hey, dude"]}' -H 'Content-Type: application/json' '0.0.0.0:45678/api/search' | \
    jq -e ".search.docs[] | .text")

echo "Returned document has the text: ${TEXT_BACK}"

curl --request GET "http://0.0.0.0:8000/v1/flow/${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"

curl --request DELETE "http://0.0.0.0:8000/v1/flow?flow_id=${FLOW_ID}" -H "accept: application/json" | jq -e ".status_code"

docker-compose -f tests/integration/jinad/test_simple_distributed_with_shards/docker-compose.yml --project-directory . down

EXPECTED_TEXT='"text:hey, dude"'

if [ "$EXPECTED_TEXT" = "$TEXT_BACK" ]; then
        echo "Success"
else
        echo "Fail"
        exit 1
fi
