# Protocol Documentation
<a name="top"></a>

## Table of Contents

- [jina.proto](#jina.proto)
    - [Chunk](#jina.Chunk)
    - [Document](#jina.Document)
    - [Envelope](#jina.Envelope)
    - [Envelope.Route](#jina.Envelope.Route)
    - [Envelope.Version](#jina.Envelope.Version)
    - [Message](#jina.Message)
    - [NdArray](#jina.NdArray)
    - [Request](#jina.Request)
    - [Request.ControlRequest](#jina.Request.ControlRequest)
    - [Request.IndexRequest](#jina.Request.IndexRequest)
    - [Request.SearchRequest](#jina.Request.SearchRequest)
    - [Request.TrainRequest](#jina.Request.TrainRequest)
    - [ScoredResult](#jina.ScoredResult)
    - [ScoredResult.Score](#jina.ScoredResult.Score)
  
    - [Envelope.Status](#jina.Envelope.Status)
    - [NdArray.QuantizationMode](#jina.NdArray.QuantizationMode)
    - [Request.ControlRequest.Command](#jina.Request.ControlRequest.Command)
  
  
    - [JinaRPC](#jina.JinaRPC)
  

- [Scalar Value Types](#scalar-value-types)



<a name="jina.proto"></a>
<p align="right"><a href="#top">Top</a></p>

## jina.proto



<a name="jina.Chunk"></a>

### Chunk
Represents a Chunk


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| doc_id | [uint32](#uint32) |  | the document ID of this chunk, universally unique |
| chunk_id | [uint32](#uint32) |  | the chunk ID, universally unique |
| text | [string](#string) |  | the original text of the chunk (only apply to the text document) |
| blob | [NdArray](#jina.NdArray) |  | the original ndarray of the chunk (apply to the image/video document) |
| raw_bytes | [bytes](#bytes) |  | raw bytes of chunk |
| embedding | [NdArray](#jina.NdArray) |  | the embedding array of this chunk |
| offset | [uint32](#uint32) |  | the offset of this chunk in the current document |
| weight | [float](#float) |  | the weight of this chunk |
| length | [uint32](#uint32) |  | the total number of chunks in the current document |
| meta_info | [bytes](#bytes) |  | some binary meta information of this chunk in bytes |
| topk_results | [ScoredResult](#jina.ScoredResult) | repeated | the top-k matched chunks |






<a name="jina.Document"></a>

### Document
Represents a Document


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| doc_id | [uint32](#uint32) |  | The unique document ID |
| raw_bytes | [bytes](#bytes) |  | the raw binary content of this document, which often represents the original document when comes into jina |
| chunks | [Chunk](#jina.Chunk) | repeated | list of the chunks of this document |
| weight | [float](#float) |  | the weight of this document |
| length | [uint32](#uint32) |  | total number of chunks in this document |
| meta_info | [bytes](#bytes) |  | some binary meta information of this chunk in bytes |
| topk_results | [ScoredResult](#jina.ScoredResult) | repeated | the top-k matched chunks |






<a name="jina.Envelope"></a>

### Envelope
Represents a Envelope, a part of the ``Message``.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| client_id | [string](#string) |  | unique id of the sender of the message |
| request_id | [uint32](#uint32) |  | unique id of the request |
| timeout | [uint32](#uint32) |  | timeout in second until this message is droped |
| routes | [Envelope.Route](#jina.Envelope.Route) | repeated | a list of routes this message goes through |
| version | [Envelope.Version](#jina.Envelope.Version) |  | version info |
| status | [Envelope.Status](#jina.Envelope.Status) |  | status info |






<a name="jina.Envelope.Route"></a>

### Envelope.Route
Represents a the route paths of this message


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| pod | [string](#string) |  | the name of the Pod |
| pod_id | [string](#string) |  | the id of the Pod |
| start_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) |  | receiving time |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) |  | sending (out) time |






<a name="jina.Envelope.Version"></a>

### Envelope.Version
Represents a the version information


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| jina | [string](#string) |  | jina&#39;s version |
| proto | [string](#string) |  | protobuf&#39;s version |
| vcs | [string](#string) |  | vcs&#39;s version |






<a name="jina.Message"></a>

### Message
Represents a Message


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| envelope | [Envelope](#jina.Envelope) |  | the envelope of the message, used internally in jina, dropped when returning to client |
| request | [Request](#jina.Request) |  | the request body |






<a name="jina.NdArray"></a>

### NdArray
Represents the a (quantized) numpy ndarray


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| raw_bytes | [bytes](#bytes) |  | the actual array data, in bytes |
| shape | [uint32](#uint32) | repeated | the shape (dimensions) of the array |
| dtype | [string](#string) |  | the data type of the array |
| quantization | [NdArray.QuantizationMode](#jina.NdArray.QuantizationMode) |  | quantization mode |
| max_val | [float](#float) |  | the max value of the ndarray |
| min_val | [float](#float) |  | the min value of the ndarray |
| scale | [float](#float) |  | the scale of the ndarray |
| original_dtype | [string](#string) |  | the original dtype of the array |






<a name="jina.Request"></a>

### Request
Represents a Request


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| request_id | [uint32](#uint32) |  | the unique ID of this request. Multiple requests with the same ID will be gathered |
| train | [Request.TrainRequest](#jina.Request.TrainRequest) |  | a train request |
| index | [Request.IndexRequest](#jina.Request.IndexRequest) |  | an index request |
| search | [Request.SearchRequest](#jina.Request.SearchRequest) |  | a search request |
| control | [Request.ControlRequest](#jina.Request.ControlRequest) |  | a control request |






<a name="jina.Request.ControlRequest"></a>

### Request.ControlRequest
Represents a control request used to control the Pod


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| command | [Request.ControlRequest.Command](#jina.Request.ControlRequest.Command) |  | the control command |






<a name="jina.Request.IndexRequest"></a>

### Request.IndexRequest
Represents an index request


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| docs | [Document](#jina.Document) | repeated | a list of Documents to index |






<a name="jina.Request.SearchRequest"></a>

### Request.SearchRequest
Represents a search request


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| docs | [Document](#jina.Document) | repeated | a list of Documents to query |
| top_k | [uint32](#uint32) |  | the number of most related results to return |






<a name="jina.Request.TrainRequest"></a>

### Request.TrainRequest
Represents a train request


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| docs | [Document](#jina.Document) | repeated | a list of Documents to train |
| flush | [bool](#bool) |  | if True then do actual training, otherwise only collect all documents but not do training. |






<a name="jina.ScoredResult"></a>

### ScoredResult
Represents an unary match result


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| match_chunk | [Chunk](#jina.Chunk) |  | the matched chunk |
| match_doc | [Document](#jina.Document) |  | the matched document |
| score | [ScoredResult.Score](#jina.ScoredResult.Score) |  | the score of this match |






<a name="jina.ScoredResult.Score"></a>

### ScoredResult.Score
Represents the score of a match


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| value | [float](#float) |  | value |
| op_name | [string](#string) |  | the name of the operator/score function |
| description | [string](#string) |  | text description of the score |
| operands | [ScoredResult.Score](#jina.ScoredResult.Score) | repeated | the score can be nested |





 


<a name="jina.Envelope.Status"></a>

### Envelope.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| SUCCESS | 0 | success |
| ERROR | 1 | error |
| PENDING | 2 | there are pending messages, more messages are followed |
| READY | 3 | ready to use |



<a name="jina.NdArray.QuantizationMode"></a>

### NdArray.QuantizationMode


| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 | no quantization is performed, stored in the original ``dtype`` |
| FP16 | 1 | 2x smaller if dtype is set to FP32 |
| UINT8 | 2 | 4x smaller but lossy when dtype is FP32 |



<a name="jina.Request.ControlRequest.Command"></a>

### Request.ControlRequest.Command


| Name | Number | Description |
| ---- | ------ | ----------- |
| TERMINATE | 0 | shutdown the Pod |
| STATUS | 1 | check the status of the Pod |


 

 


<a name="jina.JinaRPC"></a>

### JinaRPC
jina gRPC service.

| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| Call | [Request](#jina.Request) stream | [Request](#jina.Request) stream | Pass in a Request and a filled Request with topk_results will be returned. |

 



## Scalar Value Types

| .proto Type | Notes | C++ Type | Java Type | Python Type |
| ----------- | ----- | -------- | --------- | ----------- |
| <a name="double" /> double |  | double | double | float |
| <a name="float" /> float |  | float | float | float |
| <a name="int32" /> int32 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint32 instead. | int32 | int | int |
| <a name="int64" /> int64 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint64 instead. | int64 | long | int/long |
| <a name="uint32" /> uint32 | Uses variable-length encoding. | uint32 | int | int/long |
| <a name="uint64" /> uint64 | Uses variable-length encoding. | uint64 | long | int/long |
| <a name="sint32" /> sint32 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int32s. | int32 | int | int |
| <a name="sint64" /> sint64 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int64s. | int64 | long | int/long |
| <a name="fixed32" /> fixed32 | Always four bytes. More efficient than uint32 if values are often greater than 2^28. | uint32 | int | int |
| <a name="fixed64" /> fixed64 | Always eight bytes. More efficient than uint64 if values are often greater than 2^56. | uint64 | long | int/long |
| <a name="sfixed32" /> sfixed32 | Always four bytes. | int32 | int | int |
| <a name="sfixed64" /> sfixed64 | Always eight bytes. | int64 | long | int/long |
| <a name="bool" /> bool |  | bool | boolean | boolean |
| <a name="string" /> string | A string must always contain UTF-8 encoded or 7-bit ASCII text. | string | String | str/unicode |
| <a name="bytes" /> bytes | May contain any arbitrary sequence of bytes. | string | ByteString | str |

