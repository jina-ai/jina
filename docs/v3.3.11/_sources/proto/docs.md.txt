# Protocol Documentation
<a name="top"></a>

## Table of Contents

- [docarray.proto](#docarray-proto)
    - [DocumentArrayProto](#docarray-DocumentArrayProto)
  
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



<a name="docarray-DocumentArrayProto"></a>

### DocumentArrayProto
this file is just a place holder for the DA coming from docarray dependency





 

 

 

 



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
| docs | [docarray.DocumentArrayProto](#docarray-DocumentArrayProto) |  | the docs in this request |
| docs_bytes | [bytes](#bytes) |  | the docs in this request as bytes |






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
| ACTIVATE | 1 | used to add Pods to a Pod |
| DEACTIVATE | 2 | used to remove Pods from a Pod |



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

