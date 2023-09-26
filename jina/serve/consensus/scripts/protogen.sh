#/bin/sh

set -e

# This script is used to generate gRPC client stubs from the proto files.

GO_MODULE="jraft"
DOCARRAY_PROTO="docarray.proto"
DOCARRAY_DIR="../../docarray"
DOCARRAY_PACKAGE="$GO_MODULE/docarray"

JINA_PROTO="jina.proto"
JINA_DIR="../../jina"
JINA_PACKAGE="$GO_MODULE/jina-go-proto"


cd jina/proto
if ! $(grep -q '^option go_package = ' docarray.proto);then
       awk '/package docarray;/{print; print "option go_package = \"'${DOCARRAY_PACKAGE}'\";";next}1' docarray.proto > temp.proto
       mv temp.proto docarray.proto
fi
protoc --go_out=${DOCARRAY_DIR} \
       --go_opt=paths=source_relative \
       --go_opt=M${DOCARRAY_PROTO}=${DOCARRAY_PACKAGE} \
       --go-grpc_out=${DOCARRAY_DIR} \
       --go-grpc_opt=paths=source_relative \
       --experimental_allow_proto3_optional \
       ${DOCARRAY_PROTO} 

if ! $(grep -q '^option go_package = ' jina.proto);then
       awk '/package jina;/{print; print "option go_package = \"'${JINA_PACKAGE}'\";";next}1' jina.proto > temp.proto
       mv temp.proto jina.proto
fi
protoc --go_out=${JINA_DIR} \
       --go_opt=paths=source_relative \
       --go_opt=M${JINA_PROTO}=${JINA_PACKAGE} \
       --go-grpc_out=${JINA_DIR} \
       --go-grpc_opt=paths=source_relative \
       --experimental_allow_proto3_optional \
       ${JINA_PROTO} 
cd -
