# you can modify this and push to a custom repo

#GCP_PROJECT_NAME=mystical-sweep-320315
GCP_PROJECT_NAME=jina-showcase

docker build -t postgres-dumper . --no-cache
docker tag postgres-dumper gcr.io/${GCP_PROJECT_NAME}/postgres-dumper
docker push gcr.io/${GCP_PROJECT_NAME}/postgres-dumper