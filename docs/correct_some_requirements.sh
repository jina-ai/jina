#!/bin/bash

grep -rl 'opentelemetry-exporter-prometheus' extra-requirements.txt | xargs sed -i 's/opentelemetry-exporter-prometheus==1.12.0/opentelemetry-exporter-prometheus==1.12.0rc1/g'
grep -rl 'opentelemetry-exporter-otlp-proto-grpc' extra-requirements.txt | xargs sed -i 's/opentelemetry-exporter-otlp-proto-grpc==1.13.0/opentelemetry-exporter-otlp-proto-grpc==1.12.0/g'
grep -rl 'pyyaml' extra-requirements.txt | xargs sed -i 's/pyyaml==5.3.1/pyyaml==5.4.1/g'
