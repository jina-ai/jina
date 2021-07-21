#!/bin/bash

# This script is executed locally to validate if terraform apply succeeded and
# This also sets the required env-vars to be used with distributed tests.

set -e

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --action) action=true ;;
        --dir) dir="$2"; shift ;;
        --instances) instances="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z ${dir+x} ]; then
    echo -e "\n'dir' is not set. setting it to default (.)"
    dir="."
fi

if [ -z ${instances+x} ]; then
    echo -e "\n'instances' is not set. setting it to default (1)"
    instances=1
fi

COUNT=0
HOSTS=$(terraform -chdir=${dir} output -json instance_ips)

for HOST in $(echo $HOSTS | jq -r "to_entries | map(\"\(.key)=\(.value|tostring)\") | .[]" ); do
    IP=$(echo "$HOST" | rev | cut -d "=" -f1 | rev)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${IP}:8000)

    if [[ $STATUS -eq 200 ]]; then
        echo "Successfully connected to \"${HOST}:8000\", setting env var"
        COUNT=$((COUNT+1))

        if [[ "$action" = "true" ]]; then
            echo "${HOST}:8000" >> $GITHUB_ENV
        else
            export "${HOST}:8000"
        fi
    fi
done

if [[ $COUNT -eq $instances ]]; then
    echo "$instances instances successfully setup"
else
    echo "Issue in remote setup. Tried setting up $instances instances, ${COUNT} succeeded"
fi
