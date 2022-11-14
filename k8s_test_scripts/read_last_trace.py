#!/usr/bin/env python
import requests
from opentelemetry.proto.trace.v1 import trace_pb2

a = trace_pb2.TracesData()
last = int(requests.get("http://localhost:8000/v1/traces/counter").content) - 1
print(last)
a.ParseFromString(requests.get(f"http://localhost:8000/v1/traces/{last}").content)

print(a)