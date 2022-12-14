#!/bin/bash

grep -rl 'opentelemetry-exporter-prometheus' extra-requirements.txt | xargs sed -i 's/opentelemetry-exporter-prometheus==1.12.0/opentelemetry-exporter-prometheus==1.12.0rc1/g'
grep -rl 'opentelemetry-exporter-otlp-proto-grpc' extra-requirements.txt | xargs sed -i 's/opentelemetry-exporter-otlp-proto-grpc==1.13.0/opentelemetry-exporter-otlp-proto-grpc==1.13.0/g'
grep -rl 'opentelemetry-sdk' extra-requirements.txt | xargs sed -i 's/opentelemetry-sdk==1.12.0/opentelemetry-sdk==1.14.0/g'
grep -rl 'opentelemetry-semantic-conventions' extra-requirements.txt | xargs sed -i '/opentelemetry-semantic-conventions/d'
grep -rl 'opentelemetry-exporter-otlp' extra-requirements.txt | xargs sed -i '/opentelemetry-exporter-otlp/d'
grep -rl 'opentelemetry-api' extra-requirements.txt | xargs sed -i '/opentelemetry-api/d'
grep -rl 'pyyaml' extra-requirements.txt | xargs sed -i 's/pyyaml==5.3.1/pyyaml==5.4.1/g'

cat extra-requirements.txt
