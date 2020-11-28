set -e

if [ "${PWD##*/}" != "jina" ]
  then
    echo "test_integration.sh should only be run from the jina base directory"
    exit 1
fi

CONTAINER_ID=$(docker run -v /var/run/docker.sock:/var/run/docker.sock --network=host -d jinaai/test_hubapp_hubpods)

sleep 5

RESPONSE=$(curl --request POST -d '{"top_k": 10, "data": ["text:hey, dude"]}' -H 'Content-Type: application/json' '0.0.0.0:45678/api/index')

TEXT_RESPONSE=$(echo $RESPONSE | jq -e ".index.docs[] | .text")

echo "Response is: ${RESPONSE}"

# remove the new pods
docker ps -a | awk '{ print $1,$2 }' | grep hubpod:test | awk '{print $1 }' | xargs -I {} docker rm -f {}
docker rm -f $CONTAINER_ID

EXPECTED_TEXT='"text:hey, dude"'

if [ "$EXPECTED_TEXT" = "$TEXT_RESPONSE" ]; then
        echo "Success"
else
        echo "Fail"
        exit 1
fi