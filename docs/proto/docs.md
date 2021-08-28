# Protocol Documentation
<a name="top"></a>

## Table of Contents

- [jina.proto](#jina.proto)
    - [DenseNdArrayProto](#jina.DenseNdArrayProto)
    - [DocumentArrayProto](#jina.DocumentArrayProto)
    - [DocumentProto](#jina.DocumentProto)
    - [DocumentProto.EvaluationsEntry](#jina.DocumentProto.EvaluationsEntry)
    - [DocumentProto.ScoresEntry](#jina.DocumentProto.ScoresEntry)
    - [EnvelopeProto](#jina.EnvelopeProto)
    - [EnvelopeProto.CompressConfigProto](#jina.EnvelopeProto.CompressConfigProto)
    - [EnvelopeProto.VersionProto](#jina.EnvelopeProto.VersionProto)
    - [GraphProto](#jina.GraphProto)
    - [HeaderProto](#jina.HeaderProto)
    - [MessageProto](#jina.MessageProto)
    - [NamedScoreProto](#jina.NamedScoreProto)
    - [NdArrayProto](#jina.NdArrayProto)
    - [RequestProto](#jina.RequestProto)
    - [RequestProto.ControlRequestProto](#jina.RequestProto.ControlRequestProto)
    - [RequestProto.DataRequestProto](#jina.RequestProto.DataRequestProto)
    - [RouteProto](#jina.RouteProto)
    - [RoutingEdgeProto](#jina.RoutingEdgeProto)
    - [RoutingTableProto](#jina.RoutingTableProto)
    - [RoutingTableProto.PodsEntry](#jina.RoutingTableProto.PodsEntry)
    - [SparseNdArrayProto](#jina.SparseNdArrayProto)
    - [StatusProto](#jina.StatusProto)
    - [StatusProto.ExceptionProto](#jina.StatusProto.ExceptionProto)
    - [TargetPodProto](#jina.TargetPodProto)
  
    - [DenseNdArrayProto.QuantizationMode](#jina.DenseNdArrayProto.QuantizationMode)
    - [RequestProto.ControlRequestProto.Command](#jina.RequestProto.ControlRequestProto.Command)
    - [StatusProto.StatusCode](#jina.StatusProto.StatusCode)
  
    - [JinaDataRequestRPC](#jina.JinaDataRequestRPC)
    - [JinaRPC](#jina.JinaRPC)
  
- [Scalar Value Types](#scalar-value-types)



<a name="jina.proto"></a>
<p align="right"><a href="#top">Top</a></p>

## jina.proto



<a name="jina.DenseNdArrayProto"></a>

### DenseNdArrayProto
Represents a (quantized) dense n-dim array


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| buffer | [bytes](#bytes) |  | the actual array data, in bytes |
| shape | [uint32](#uint32) | repeated | the shape (dimensions) of the array |
| dtype | [string](#string) |  | the data type of the array |
| quantization | [DenseNdArrayProto.QuantizationMode](#jina.DenseNdArrayProto.QuantizationMode) |  | quantization mode |
| max_val | [float](#float) |  | the max value of the ndarray |
| min_val | [float](#float) |  | the min value of the ndarray |
| scale | [float](#float) |  | the scale of the ndarray |
| original_dtype | [string](#string) |  | the original dtype of the array |






<a name="jina.DocumentArrayProto"></a>

### DocumentArrayProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| docs | [DocumentProto](#jina.DocumentProto) | repeated | a list of Documents |






<a name="jina.DocumentProto"></a>

### DocumentProto
Represents a Document


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| id | [string](#string) |  | A hexdigest that represents a unique document ID |
| granularity | [uint32](#uint32) |  | the depth of the recursive chunk structure |
| adjacency | [uint32](#uint32) |  | the width of the recursive match structure |
| parent_id | [string](#string) |  | the parent id from the previous granularity |
| buffer | [bytes](#bytes) |  | the raw binary content of this document, which often represents the original document when comes into jina |
| blob | [NdArrayProto](#jina.NdArrayProto) |  | the ndarray of the image/audio/video document |
| text | [string](#string) |  | a text document |
| uri | [string](#string) |  | a uri of the document could be: a local file path, a remote url starts with http or https or data URI scheme |
| graph | [GraphProto](#jina.GraphProto) |  | Related information to be used when a Document represents a graph with its chunks as nodes |
| chunks | [DocumentProto](#jina.DocumentProto) | repeated | list of the sub-documents of this document (recursive structure) |
| weight | [float](#float) |  | The weight of this document |
| matches | [DocumentProto](#jina.DocumentProto) | repeated | the matched documents on the same level (recursive structure) |
| mime_type | [string](#string) |  | mime type of this document, for buffer content, this is required; for other contents, this can be guessed |
| tags | [google.protobuf.Struct](#google.protobuf.Struct) |  | a structured data value, consisting of field which map to dynamically typed values. |
| location | [uint32](#uint32) | repeated | the position of the doc, could be start and end index of a string; could be x,y (top, left) coordinate of an image crop; could be timestamp of an audio clip |
| offset | [uint32](#uint32) |  | the offset of this doc in the previous granularity document |
| embedding | [NdArrayProto](#jina.NdArrayProto) |  | the embedding `ndarray` of this document |
| scores | [DocumentProto.ScoresEntry](#jina.DocumentProto.ScoresEntry) | repeated | Scores performed on the document, each element corresponds to a metric |
| modality | [string](#string) |  | modality, an identifier to the modality this document belongs to. In the scope of multi/cross modal search |
| evaluations | [DocumentProto.EvaluationsEntry](#jina.DocumentProto.EvaluationsEntry) | repeated | Evaluations performed on the document, each element corresponds to a metric |






<a name="jina.DocumentProto.EvaluationsEntry"></a>

### DocumentProto.EvaluationsEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) |  |  |
| value | [NamedScoreProto](#jina.NamedScoreProto) |  |  |






<a name="jina.DocumentProto.ScoresEntry"></a>

### DocumentProto.ScoresEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) |  |  |
| value | [NamedScoreProto](#jina.NamedScoreProto) |  |  |






<a name="jina.EnvelopeProto"></a>

### EnvelopeProto
Represents a Envelope, a part of the ``Message``.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| sender_id | [string](#string) |  | unique id of the sender of the message |
| receiver_id | [string](#string) |  | unique id of the receiver of the message, only used in router-dealer pattern |
| request_id | [string](#string) |  | unique id of the request |
| timeout | [uint32](#uint32) |  | timeout in second until this message is dropped |
| version | [EnvelopeProto.VersionProto](#jina.EnvelopeProto.VersionProto) |  | version info |
| request_type | [string](#string) |  | type of the request: DataRequest, ControlRequest |
| check_version | [bool](#bool) |  | check local Protobuf version on every Pod that this message flows to |
| compression | [EnvelopeProto.CompressConfigProto](#jina.EnvelopeProto.CompressConfigProto) |  | compress configuration used for request |
| routes | [RouteProto](#jina.RouteProto) | repeated | status info on every routes |
| routing_table | [RoutingTableProto](#jina.RoutingTableProto) |  | the routing table contains information to the next pods |
| status | [StatusProto](#jina.StatusProto) |  | status info |
| header | [HeaderProto](#jina.HeaderProto) |  | header contains meta info defined by the user, copied from Request, for lazy serialization |






<a name="jina.EnvelopeProto.CompressConfigProto"></a>

### EnvelopeProto.CompressConfigProto
Represents a config for the compression algorithm


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| algorithm | [string](#string) |  | compress algorithm used for request |
| min_bytes | [uint64](#uint64) |  | the high watermark that triggers the message compression. message bigger than this HWM (in bytes) will be compressed by the algorithm. |
| min_ratio | [float](#float) |  | the low watermark that enables the sending of a compressed message. compression rate (after_size/before_size) lower than this LWM will be considered as successeful compression, and will be sent. Otherwise, it will send the original message without compression |
| parameters | [google.protobuf.Struct](#google.protobuf.Struct) |  | other parameters that can be accepted by the algorithm |






<a name="jina.EnvelopeProto.VersionProto"></a>

### EnvelopeProto.VersionProto
Represents a the version information


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| jina | [string](#string) |  | jina&#39;s version |
| proto | [string](#string) |  | protobuf&#39;s version |
| vcs | [string](#string) |  | vcs&#39;s version |






<a name="jina.GraphProto"></a>

### GraphProto
Represents a Graph


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| adjacency | [SparseNdArrayProto](#jina.SparseNdArrayProto) |  | adjacency list |
| edge_features | [google.protobuf.Struct](#google.protobuf.Struct) |  | Container structure to store edge features |
| undirected | [bool](#bool) |  | Flag indicating if the graph is to be interpreted as an undirected graph |






<a name="jina.HeaderProto"></a>

### HeaderProto
Represents a Header.
- The header&#39;s content will be defined by the user request.
- It will be copied to the envelope.header
- In-flow operations will modify the envelope.header
- While returning, copy envelope.header back to request.header


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| exec_endpoint | [string](#string) |  | the endpoint specified by `@requests(on=&#39;/abc&#39;)` |
| target_peapod | [string](#string) |  | if set, the request is targeted to certain peas/pods, regex strings |
| no_propagate | [bool](#bool) |  | if set, then this request is not propagate over the Flow topology |






<a name="jina.MessageProto"></a>

### MessageProto
Represents a Message


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| envelope | [EnvelopeProto](#jina.EnvelopeProto) |  | the envelope of the message, used internally in jina, dropped when returning to client |
| request | [RequestProto](#jina.RequestProto) |  | the request body |






<a name="jina.NamedScoreProto"></a>

### NamedScoreProto
Represents the relevance model to `ref_id`


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| value | [float](#float) |  | value |
| op_name | [string](#string) |  | the name of the operator/score function |
| description | [string](#string) |  | text description of the score |
| operands | [NamedScoreProto](#jina.NamedScoreProto) | repeated | the score can be nested |
| ref_id | [string](#string) |  | the score is computed between doc `id` and `ref_id` |






<a name="jina.NdArrayProto"></a>

### NdArrayProto
Represents a general n-dim array, can be either dense or sparse


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| dense | [DenseNdArrayProto](#jina.DenseNdArrayProto) |  | dense representation of the ndarray |
| sparse | [SparseNdArrayProto](#jina.SparseNdArrayProto) |  | sparse representation of the ndarray |






<a name="jina.RequestProto"></a>

### RequestProto
Represents a Request


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| request_id | [string](#string) |  | the unique ID of this request. Multiple requests with the same ID will be gathered |
| control | [RequestProto.ControlRequestProto](#jina.RequestProto.ControlRequestProto) |  | a control request |
| data | [RequestProto.DataRequestProto](#jina.RequestProto.DataRequestProto) |  | a data request |
| header | [HeaderProto](#jina.HeaderProto) |  | header contains meta info defined by the user |
| parameters | [google.protobuf.Struct](#google.protobuf.Struct) |  | extra kwargs that will be used in executor |
| routes | [RouteProto](#jina.RouteProto) | repeated | status info on every routes |
| status | [StatusProto](#jina.StatusProto) |  | status info |






<a name="jina.RequestProto.ControlRequestProto"></a>

### RequestProto.ControlRequestProto
Represents a control request used to control the BasePod


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| command | [RequestProto.ControlRequestProto.Command](#jina.RequestProto.ControlRequestProto.Command) |  | the control command |






<a name="jina.RequestProto.DataRequestProto"></a>

### RequestProto.DataRequestProto
Represents a general data request


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| docs | [DocumentProto](#jina.DocumentProto) | repeated | a list of Documents to query |
| groundtruths | [DocumentProto](#jina.DocumentProto) | repeated | a list of groundtruth Document you want to evaluate it with |






<a name="jina.RouteProto"></a>

### RouteProto
Represents a the route paths of this message


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| pod | [string](#string) |  | the name of the BasePod |
| pod_id | [string](#string) |  | the id of the BasePod |
| start_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) |  | receiving time |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) |  | sending (out) time |
| status | [StatusProto](#jina.StatusProto) |  | the status of the execution |






<a name="jina.RoutingEdgeProto"></a>

### RoutingEdgeProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| pod | [string](#string) |  |  |
| send_as_bind | [bool](#bool) |  |  |






<a name="jina.RoutingTableProto"></a>

### RoutingTableProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| pods | [RoutingTableProto.PodsEntry](#jina.RoutingTableProto.PodsEntry) | repeated | Pods that get visited during a Flow. Gateway should be both the first and the last entry. |
| active_pod | [string](#string) |  | The currently active Pod. Needed for ZMQ. |






<a name="jina.RoutingTableProto.PodsEntry"></a>

### RoutingTableProto.PodsEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) |  |  |
| value | [TargetPodProto](#jina.TargetPodProto) |  |  |






<a name="jina.SparseNdArrayProto"></a>

### SparseNdArrayProto
Represents a sparse ndarray


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| indices | [DenseNdArrayProto](#jina.DenseNdArrayProto) |  | A 2-D int64 tensor of shape [N, ndims], which specifies the indices of the elements in the sparse tensor that contain nonzero values (elements are zero-indexed) |
| values | [DenseNdArrayProto](#jina.DenseNdArrayProto) |  | A 1-D tensor of any type and shape [N], which supplies the values for each element in indices. |
| shape | [uint32](#uint32) | repeated | A 1-D int64 tensor of shape [ndims], which specifies the shape of the sparse tensor. |






<a name="jina.StatusProto"></a>

### StatusProto
Represents a Status


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| code | [StatusProto.StatusCode](#jina.StatusProto.StatusCode) |  | status code |
| description | [string](#string) |  | error description of the very first exception |
| exception | [StatusProto.ExceptionProto](#jina.StatusProto.ExceptionProto) |  | the details of the error |






<a name="jina.StatusProto.ExceptionProto"></a>

### StatusProto.ExceptionProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| name | [string](#string) |  | the class name of the exception |
| args | [string](#string) | repeated | the list of arguments given to the exception constructor. |
| stacks | [string](#string) | repeated | the exception traceback stacks |
| executor | [string](#string) |  | the name of the executor bind to that peapod (if applicable) |






<a name="jina.TargetPodProto"></a>

### TargetPodProto



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| host | [string](#string) |  | the host HeadPea of the BasePod |
| port | [uint32](#uint32) |  | the port HeadPea of the BasePod |
| port_out | [uint32](#uint32) |  | the port TailPea of the BasePod |
| expected_parts | [uint32](#uint32) |  | the number of parts the pod should expect |
| out_edges | [RoutingEdgeProto](#jina.RoutingEdgeProto) | repeated | pod_name of Pods, the TailPea should send traffic to |
| target_identity | [string](#string) |  |  |





 


<a name="jina.DenseNdArrayProto.QuantizationMode"></a>

### DenseNdArrayProto.QuantizationMode


| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 | no quantization is performed, stored in the original ``dtype`` |
| FP16 | 1 | 2x smaller if dtype is set to FP32 |
| UINT8 | 2 | 4x smaller but lossy when dtype is FP32 |



<a name="jina.RequestProto.ControlRequestProto.Command"></a>

### RequestProto.ControlRequestProto.Command


| Name | Number | Description |
| ---- | ------ | ----------- |
| TERMINATE | 0 | shutdown the BasePod |
| STATUS | 1 | check the status of the BasePod |
| IDLE | 2 | used in ROUTER-DEALER pattern, tells the router that the dealer is idle |
| CANCEL | 3 | used in ROUTER-DEALER pattern, tells the router that the dealer is busy (or closed) |
| SCALE | 4 | scale up/down a Pod |
| ACTIVATE | 5 | used in ROUTER-DEALER pattern, Indicate a Pea that it can activate itself and send the IDLE command to their router |
| DEACTIVATE | 6 | used in ROUTER-DEALER pattern, Indicate a Pea that it can deactivate itself and send the CANCEL command to their router |



<a name="jina.StatusProto.StatusCode"></a>

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


 

 


<a name="jina.JinaDataRequestRPC"></a>

### JinaDataRequestRPC
jina gRPC service for DataRequests.

| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| Call | [MessageProto](#jina.MessageProto) | [.google.protobuf.Empty](#google.protobuf.Empty) | Pass in a Message, wrapping a DataRequest |


<a name="jina.JinaRPC"></a>

### JinaRPC
jina gRPC service.

| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| Call | [RequestProto](#jina.RequestProto) stream | [RequestProto](#jina.RequestProto) stream | Pass in a Request and a filled Request with matches will be returned. |

 



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

