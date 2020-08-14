docker build --build-arg PIP_TAG="[devel]" -f Dockerfiles/pip.Dockerfile -t jinaai/jina:test-pip .

pip install pytest
pip install pytest-xdist
pip install pytest-timeout
pip install pytest-cov
pytest --cov=jina --cov-report=xml -n 1 --timeout=60 -v tests/unit
