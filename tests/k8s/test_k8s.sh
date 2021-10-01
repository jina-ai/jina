set -ex

docker build --build-arg PIP_TAG="[devel]" -f Dockerfiles/pip.Dockerfile -t jinaai/jina:test-pip .
if [ "${PWD##*/}" != "jina" ]
  then
    echo "test_k8s.sh should only be run from the jina base directory"
    exit 1
fi

pip install pytest
pip install numpy
export JINA_K8S_USE_TEST_PIP=True
pytest --suppress-no-test-exit-code --force-flaky --min-passes 1 --max-runs 5 --cov=jina --cov-report=xml --timeout=3600 ./tests/k8s/test_k8s.py
pytest --suppress-no-test-exit-code --force-flaky --min-passes 1 --max-runs 5 --cov=jina --cov-report=xml --timeout=3600 ./tests/k8s/test_custom_resource_dir.py
