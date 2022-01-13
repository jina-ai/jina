# Protocol Documentation
<a name="top"></a>

## Table of Contents

- [docarray.proto](#docarray-proto)
    - [DenseNdArrayProto](#docarray-DenseNdArrayProto)
    - [DocumentArrayProto](#docarray-DocumentArrayProto)
    - [DocumentProto](#docarray-DocumentProto)
    - [DocumentProto.EvaluationsEntry](#docarray-DocumentProto-EvaluationsEntry)
    - [DocumentProto.ScoresEntry](#docarray-DocumentProto-ScoresEntry)
    - [GraphProto](#docarray-GraphProto)
    - [NamedScoreProto](#docarray-NamedScoreProto)
    - [NdArrayProto](#docarray-NdArrayProto)
    - [SparseNdArrayProto](#docarray-SparseNdArrayProto)
  
- [jina.proto](#jina-proto)
    - [ControlRequestProto](#jina-ControlRequestProto)
    - [DataRequestListProto](#jina-DataRequestListProto)
    - [DataRequestProto](#jina-DataRequestProto)
    - [DataRequestProto.DataContentProto](#jina-DataRequestProto-DataContentProto)
    - [HeaderProto](#jina-HeaderProto)
    - [RelatedEntity](#jina-RelatedEntity)
    - [RouteProto](#jina-RouteProto)
    - [StatusProto](#jina-StatusProto)
    - [StatusProto.ExceptionProto](#jina-StatusProto-ExceptionProto)
  
    - [ControlRequestProto.Command](#jina-ControlRequestProto-Command)
    - [StatusProto.StatusCode](#jina-StatusProto-StatusCode)
  
    - [JinaControlRequestRPC](#jina-JinaControlRequestRPC)
    - [JinaDataRequestRPC](#jina-JinaDataRequestRPC)
    - [JinaRPC](#jina-JinaRPC)
    - [JinaSingleDataRequestRPC](#jina-JinaSingleDataRequestRPC)
  
- [Scalar Value Types](#scalar-value-types)



<a name="docarray-proto"></a>
<p align="right"><a href="#top">Top</a></p>

## docarray.proto



<a name="docarray-DenseNdArrayProto"></a>

### DenseNdArrayProto
Represents a (quantized) dense n-dim array


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| buffer | [bytes](#bytes) |  | the actual array data, in bytes |
| shape | [uint32](#uint32) | repeated | the shape (dimensions) of the array |
| dtype | [string](#string) |  | the data type of the array |






<a name="docarray-DocumentArrayProto"></a>

### DocumentArrayProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| docs | [DocumentProto](#docarray-DocumentProto) | repeated | a list of Documents |






<a name="docarray-DocumentProto"></a>

### DocumentProto
Represents a Document


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| id | [string](#string) |  | A hexdigest that represents a unique document ID |
| granularity | [uint32](#uint32) |  | the depth of the recursive chunk structure |
| adjacency | [uint32](#uint32) |  | the width of the recursive match structure |
| parent_id | [string](#string) |  | the parent id from the previous granularity |
| buffer | [bytes](#bytes) |  | the raw binary content of this document, which often represents the original document when comes into jina |
| blob | [NdArrayProto](#docarray-NdArrayProto) |  | the ndarray of the image/audio/video document |
| text | [string](#string) |  | a text document |
| chunks | [DocumentProto](#docarray-DocumentProto) | repeated | list of the sub-documents of this document (recursive structure) |
| weight | [float](#float) |  | The weight of this document |
| matches | [DocumentProto](#docarray-DocumentProto) | repeated | the matched documents on the same level (recursive structure) |
| uri | [string](#string) |  | a uri of the document could be: a local file path, a remote url starts with http or https or data URI scheme |
| mime_type | [string](#string) |  | mime type of this document, for buffer content, this is required; for other contents, this can be guessed |
| tags | [google.protobuf.Struct](#google-protobuf-Struct) |  | a structured data value, consisting of field which map to dynamically typed values. |
| location | [float](#float) | repeated | the position of the doc, could be start and end index of a string; could be x,y (top, left) coordinate of an image crop; could be timestamp of an audio clip |
| offset | [float](#float) |  | the offset of this doc in the previous granularity document |
| embedding | [NdArrayProto](#docarray-NdArrayProto) |  | the embedding `ndarray` of this document |
| scores | [DocumentProto.ScoresEntry](#docarray-DocumentProto-ScoresEntry) | repeated | Scores performed on the document, each element corresponds to a metric |
| modality | [string](#string) |  | modality, an identifier to the modality this document belongs to. In the scope of multi/cross modal search |
| evaluations | [DocumentProto.EvaluationsEntry](#docarray-DocumentProto-EvaluationsEntry) | repeated | Evaluations performed on the document, each element corresponds to a metric |






<a name="docarray-DocumentProto-EvaluationsEntry"></a>

### DocumentProto.EvaluationsEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) |  |  |
| value | [NamedScoreProto](#docarray-NamedScoreProto) |  |  |






<a name="docarray-DocumentProto-ScoresEntry"></a>

### DocumentProto.ScoresEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) |  |  |
| value | [NamedScoreProto](#docarray-NamedScoreProto) |  |  |






<a name="docarray-GraphProto"></a>

### GraphProto
Represents a Graph


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| adjacency | [NdArrayProto](#docarray-NdArrayProto) |  | adjacency list |
| edge_features | [google.protobuf.Struct](#google-protobuf-Struct) |  | Container structure to store edge features |
| undirected | [bool](#bool) |  | Flag indicating if the graph is to be interpreted as an undirected graph |






<a name="docarray-NamedScoreProto"></a>

### NamedScoreProto
Represents the relevance model to `ref_id`


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| value | [float](#float) |  | value |
| op_name | [string](#string) |  | the name of the operator/score function |
| description | [string](#string) |  | text description of the score |
| operands | [NamedScoreProto](#docarray-NamedScoreProto) | repeated | the score can be nested |
| ref_id | [string](#string) |  | the score is computed between doc `id` and `ref_id` |






<a name="docarray-NdArrayProto"></a>

### NdArrayProto
Represents a general n-dim array, can be either dense or sparse


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| dense | [DenseNdArrayProto](#docarray-DenseNdArrayProto) |  | dense representation of the ndarray |
| sparse | [SparseNdArrayProto](#docarray-SparseNdArrayProto) |  | sparse representation of the ndarray |
| cls_name | [string](#string) |  | the name of the ndarray class |
| parameters | [google.protobuf.Struct](#google-protobuf-Struct) |  |  |






<a name="docarray-SparseNdArrayProto"></a>

### SparseNdArrayProto
Represents a sparse ndarray


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| indices | [DenseNdArrayProto](#docarray-DenseNdArrayProto) |  | A 2-D int64 tensor of shape [N, ndims], which specifies the indices of the elements in the sparse tensor that contain nonzero values (elements are zero-indexed) |
| values | [DenseNdArrayProto](#docarray-DenseNdArrayProto) |  | A 1-D tensor of any type and shape [N], which supplies the values for each element in indices. |
| shape | [uint32](#uint32) | repeated | A 1-D int64 tensor of shape [ndims], which specifies the shape of the sparse tensor. |





 

 

 

 



<a name="jina-proto"></a>
<p align="right"><a href="#top">Top</a></p>

## jina.proto



<a name="jina-ControlRequestProto"></a>

### ControlRequestProto
Represents a ControlRequest


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [HeaderProto](#jina-HeaderProto) |  | header contains meta info defined by the user |
| command | [ControlRequestProto.Command](#jina-ControlRequestProto-Command) |  | the control command |
| relatedEntities | [RelatedEntity](#jina-RelatedEntity) | repeated | list of entities this ControlMessage is related to |






<a name="jina-DataRequestListProto"></a>

### DataRequestListProto
Represents a list of data requests
This should be replaced by streaming


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| requests | [DataRequestProto](#jina-DataRequestProto) | repeated | requests in this list |






<a name="jina-DataRequestProto"></a>

### DataRequestProto
Represents a DataRequest


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [HeaderProto](#jina-HeaderProto) |  | header contains meta info defined by the user |
| parameters | [google.protobuf.Struct](#google-protobuf-Struct) |  | extra kwargs that will be used in executor |
| routes | [RouteProto](#jina-RouteProto) | repeated | status info on every routes |
| data | [DataRequestProto.DataContentProto](#jina-DataRequestProto-DataContentProto) |  | container for docs and groundtruths |






<a name="jina-DataRequestProto-DataContentProto"></a>

### DataRequestProto.DataContentProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| docs | [docarray.DocumentProto](#docarray-DocumentProto) | repeated | the docs in this request |
| groundtruths | [docarray.DocumentProto](#docarray-DocumentProto) | repeated | a list of groundtruth Documents |






<a name="jina-HeaderProto"></a>

### HeaderProto
Represents a Header.
- The header&#39;s content will be defined by the user request.
- It will be copied to the envelope.header
- In-flow operations will modify the envelope.header
- While returning, copy envelope.header back to request.header


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| request_id | [string](#string) |  | the unique ID of this request. Multiple requests with the same ID will be gathered |
| status | [StatusProto](#jina-StatusProto) |  | status info |
| exec_endpoint | [string](#string) | optional | the endpoint specified by `@requests(on=&#39;/abc&#39;)` |
| target_executor | [string](#string) | optional | if set, the request is targeted to certain executor, regex strings |
| timeout | [uint32](#uint32) | optional | epoch time in seconds after which the request should be dropped |






<a name="jina-RelatedEntity"></a>

### RelatedEntity
Represents an entity (like an ExecutorRuntime)


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| id | [string](#string) |  | unique id of the entity, like the name of a pea |
| address | [string](#string) |  | address of the entity, could be an IP address, domain name etc, does not include port |
| port | [uint32](#uint32) |  | port this entity is listening on |
| shard_id | [uint32](#uint32) | optional | the id of the shard it belongs to, if it is a shard |






<a name="jina-RouteProto"></a>

### RouteProto
Represents a the route paths of this message as perceived by the Gateway
start_time is set when the Gateway sends a message to a Pod
end_time is set when the Gateway receives a message from a Pod
thus end_time - start_time includes Executor computation, runtime overhead, serialization and network


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| executor | [string](#string) |  | the name of the BasePod |
| start_time | [google.protobuf.Timestamp](#google-protobuf-Timestamp) |  | time when the Gateway starts sending to the Pod |
| end_time | [google.protobuf.Timestamp](#google-protobuf-Timestamp) |  | time when the Gateway received it from the Pod |
| status | [StatusProto](#jina-StatusProto) |  | the status of the execution |






<a name="jina-StatusProto"></a>

### StatusProto
Represents a Status


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| code | [StatusProto.StatusCode](#jina-StatusProto-StatusCode) |  | status code |
| description | [string](#string) |  | error description of the very first exception |
| exception | [StatusProto.ExceptionProto](#jina-StatusProto-ExceptionProto) |  | the details of the error |






<a name="jina-StatusProto-ExceptionProto"></a>

### StatusProto.ExceptionProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| name | [string](#string) |  | the class name of the exception |
| args | [string](#string) | repeated | the list of arguments given to the exception constructor. |
| stacks | [string](#string) | repeated | the exception traceback stacks |
| executor | [string](#string) |  | the name of the executor bind to that peapod (if applicable) |





 


<a name="jina-ControlRequestProto-Command"></a>

### ControlRequestProto.Command


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS | 0 | check the status of the BasePod |
| ACTIVATE | 1 | used to add Peas to a Pod |
| DEACTIVATE | 2 | used to remove Peas from a Pod |



<a name="jina-StatusProto-StatusCode"></a>

### StatusProto.StatusCode


| Name | Number | Description |
| ---- | ------ | ----------- |
| SUCCESS | 0 | success |
| PENDING | 1 | there are pending messages, more messages are followed |
| READY | 2 | ready to use |
| ERROR | 3 | error |
| ERROR_DUPLICATE | 4 | already a existing pod running |
| ERROR_NOTALLOWED | 5 | not allowed to open pod remotely |
| ERROR_CHAINED | 6 | chained from the previous error |


 

 


<a name="jina-JinaControlRequestRPC"></a>

### JinaControlRequestRPC
jina gRPC service for ControlRequests.

| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| process_control | [ControlRequestProto](#jina-ControlRequestProto) | [ControlRequestProto](#jina-ControlRequestProto) | Used for passing ControlRequests to the Executors |


<a name="jina-JinaDataRequestRPC"></a>

### JinaDataRequestRPC
jina gRPC service for DataRequests.

| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| process_data | [DataRequestListProto](#jina-DataRequestListProto) | [DataRequestProto](#jina-DataRequestProto) | Used for passing DataRequests to the Executors |


<a name="jina-JinaRPC"></a>

### JinaRPC
jina Gateway gRPC service.

| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| Call | [DataRequestProto](#jina-DataRequestProto) stream | [DataRequestProto](#jina-DataRequestProto) stream | Pass in a Request and a filled Request with matches will be returned. |


<a name="jina-JinaSingleDataRequestRPC"></a>

### JinaSingleDataRequestRPC
jina gRPC service for DataRequests.
This is used to send requests to Executors when a list of requests is not needed

| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| process_single_data | [DataRequestProto](#jina-DataRequestProto) | [DataRequestProto](#jina-DataRequestProto) | Used for passing DataRequests to the Executors |

 



## Scalar Value Types

| .proto Type | Notes | C++ | Java | Python | Go | C# | PHP | Ruby |
| ----------- | ----- | --- | ---- | ------ | -- | -- | --- | ---- |
| <a name="double" /> double |  | double | double | float | float64 | double | float | Float |
| <a name="float" /> float |  | float | float | float | float32 | float | float | Float |
| <a name="int32" /> int32 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint32 instead. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="int64" /> int64 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint64 instead. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="uint32" /> uint32 | Uses variable-length encoding. | uint32 | int | int/long | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="uint64" /> uint64 | Uses variable-length encoding. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum or Fixnum (as required) |
| <a name="sint32" /> sint32 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int32s. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sint64" /> sint64 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int64s. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="fixed32" /> fixed32 | Always four bytes. More efficient than uint32 if values are often greater than 2^28. | uint32 | int | int | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="fixed64" /> fixed64 | Always eight bytes. More efficient than uint64 if values are often greater than 2^56. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum |
| <a name="sfixed32" /> sfixed32 | Always four bytes. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sfixed64" /> sfixed64 | Always eight bytes. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="bool" /> bool |  | bool | boolean | boolean | bool | bool | boolean | TrueClass/FalseClass |
| <a name="string" /> string | A string must always contain UTF-8 encoded or 7-bit ASCII text. | string | String | str/unicode | string | string | string | String (UTF-8) |
| <a name="bytes" /> bytes | May contain any arbitrary sequence of bytes. | string | ByteString | str | []byte | ByteString | string | String (ASCII-8BIT) |

