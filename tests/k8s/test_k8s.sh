set -ex

docker build --build-arg PIP_TAG="[devel]" -f Dockerfiles/pip.Dockerfile -t jinaai/jina:test-pip .
if [ "${PWD##*/}" != "jina" ]
  then
    echo "test_k8s.sh should only be run from the jina base directory"
    exit 1
fi

pip install pytest
pip install numpy

pytest -sv ./tests/k8s/test_k8s.py
pytest -sv ./tests/k8s/test_custom_resource_dir.py

