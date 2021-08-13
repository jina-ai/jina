# you can modify this and push to a custom repo

#GCP_PROJECT_NAME=mystical-sweep-320315
GCP_PROJECT_NAME=jina-showcase

docker build -t match-merger . --no-cache
docker tag match-merger gcr.io/${GCP_PROJECT_NAME}/match-merger
docker push gcr.io/${GCP_PROJECT_NAME}/match-merger