# you can modify this and push to a custom repo

GCP_PROJECT_NAME=mystical-sweep-320315

docker build -t match-merger .
docker tag match-merger gcr.io/${GCP_PROJECT_NAME}/match-merger
docker push gcr.io/${GCP_PROJECT_NAME}/match-merger