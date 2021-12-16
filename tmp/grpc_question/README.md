protoc test.proto --python_out=.
pytest -v -s test_serialization.py 
