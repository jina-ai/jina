package main

import (
    "context"
//     "fmt"
//     "os"
     "io"
//     "io/ioutil"
     "log"
     "sync"
     "unsafe"
//     "time"
     "errors"
      "reflect"

    "google.golang.org/protobuf/proto"
//     "google.golang.org/protobuf/types/known/emptypb"
    empty "github.com/golang/protobuf/ptypes/empty"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
)

/*

#cgo pkg-config: python3
#include <Python.h>

static PyObject* call_python_function(const char* module_name, const char* function_name, PyObject* WorkerRequestHandlersArgs) {
    PyObject* function;
    PyObject* args;
    PyObject* result;
    PyObject* module;
    module = PyImport_ImportModule(module_name);
    function = PyObject_GetAttrString(module, function_name);
    result = PyObject_CallFunctionObjArgs(function, WorkerRequestHandlersArgs, NULL);
    return result;
}

static PyObject* call_handle_binary_request(PyObject* function, PyObject* WorkerRequestHandlersArgs, PyObject* BinaryData) {
    PyObject* result;
    result = PyObject_CallFunctionObjArgs(function, WorkerRequestHandlersArgs, BinaryData, NULL);
    return result;
}
*/
import "C"

type executorFSM struct {
    //executor *executor
    executor   *C.PyObject
    module     *C.PyObject
    handle_binary_request_func *C.PyObject
    mtx      sync.RWMutex
    snapshot *snapshot
    write_endpoints  []string
}


func NewExecutorFSM(target string, Worker *C.PyObject) *executorFSM {
    log.Printf("Avoiding compilation error %v", target)
    module := C.PyImport_ImportModule(C.CString("jina.serve.runtimes.worker.request_handling"))
    function := C.PyObject_GetAttrString(module, C.CString("handle_binary_request"));
    write_endpoints := C.call_python_function(C.CString("jina.serve.runtimes.worker.request_handling"), C.CString("get_write_endpoints"), Worker)
    ret := C.call_python_function(C.CString("jina.serve.runtimes.worker.request_handling"), C.CString("call_try_one_thing"), Worker)
    log.Printf("I need to find a way to convert this PyObject into a List of strings %v", write_endpoints)
    log.Printf("ret %v", ret)

    var WriteEndpoints []string
    for i := 0; i < int(C.PyList_Size(write_endpoints)); i++ {
        item := C.PyList_GetItem(write_endpoints, C.long(i))
        py_str := C.PyUnicode_AsUTF8String(item)
        //defer C.Py_DECREF(py_str)
        if (py_str == nil) {
            log.Printf("Failed to convert item to string")
            return nil
        }
        var go_str string
        c_str := C.PyBytes_AsString(py_str)
        header := (*reflect.StringHeader)(unsafe.Pointer(&go_str))
        header.Data = uintptr(unsafe.Pointer(c_str))
        header.Len = int(C.PyBytes_Size(py_str))
        WriteEndpoints = append(WriteEndpoints, go_str)
    }
    log.Printf("WRITE ENDPOINTS %v", WriteEndpoints)
    return &executorFSM{
        executor: Worker,
        module: module,
        handle_binary_request_func: function,
        write_endpoints: WriteEndpoints,
    }
}

func (executor *executorFSM) isSnapshotInProgress() bool {
    if executor.snapshot != nil &&
        *executor.snapshot.status == pb.SnapshotStatusProto_RUNNING {
        return true
    }
    return false
}

// triggered once the followers have committed the log
func (fsm *executorFSM) Apply(l *raft.Log) interface{} {
    log.Printf("executorFSM method Apply")
    fsm.mtx.Lock()
    // TODO: Learn how to extract l.data and pass bytes to Python and back, in Python load DataRequest from those bytes and also here
    defer fsm.mtx.Unlock()
    log.Printf("Length Data %v", len(l.Data))
    cstr := (*C.char)(unsafe.Pointer(&l.Data[0]))
    pyBytes := C.PyBytes_FromStringAndSize(cstr, C.long(len(l.Data)))
    ret := C.call_handle_binary_request(fsm.handle_binary_request_func, fsm.executor, pyBytes)
    log.Printf("ret %v", ret)
//     if (C.PyBytes_Check(ret) == 0) {
//         fmt.Println("Object is not a bytes object")
//         return
//     }
    var go_bytes []byte
    c_bytes := C.PyBytes_AsString(ret)
    length := C.PyBytes_Size(ret)
    header := (*reflect.SliceHeader)(unsafe.Pointer(&go_bytes))
    header.Data = uintptr(unsafe.Pointer(c_bytes))
    header.Len = int(length)
    header.Cap = int(length)
    response := &pb.DataRequestProto{}
    err := proto.Unmarshal(go_bytes, response)
    if err != nil {
        log.Printf("EROR UNMARSHALLING RESPONSE FROM PYTHON: %v", err)
        return err
    }
    return response
//     for {
//         if !fsm.isSnapshotInProgress() {
//             // we need not to return error but make it slow, wait until not anymore in progress
//             break
//         }
//         log.Printf("cannot execute Apply because a snapshot is in progress")
//         time.Sleep(1 * time.Second)
//     }
//     if fsm.isSnapshotInProgress() {
//         // we need not to return error but make it slow, wait until not anymore in progress
//         log.Printf("cannot execute Apply because a snapshot is in progress")
//         return fmt.Errorf("Cannot accept new requests when snap shotting is in progress.")
//     }
//     log.Printf("calling underlying executor")
//     conn, err := fsm.executor.newConnection()
//     if err != nil {
//         return err
//     }
//     defer conn.Close()
//     client := pb.NewJinaSingleDataRequestRPCClient(conn)
//     dataRequestProto := &pb.DataRequestProto{}
//     err = proto.Unmarshal(l.Data, dataRequestProto)
//     if err != nil {
//         log.Print("unmarshaling error: ", err)
//         return err
//     }
//
//     response, err := client.ProcessSingleData(context.Background(), dataRequestProto)
//     if err != nil {
//         log.Printf("error calling executor: %v", err)
//         return err
//     }
//
//     return response
}

func (fsm *executorFSM) Snapshot() (raft.FSMSnapshot, error) {
    // Make sure that any future calls to f.Apply() don't change the snapshot.
    log.Printf("executorFSM method Snapshot")
    fsm.mtx.Lock()
    defer fsm.mtx.Unlock()
    return nil, nil
//     log.Printf("calling underlying executor")
//     conn, err := fsm.executor.newConnection()
//     if err != nil {
//         return nil, err
//     }
//     defer conn.Close()
//     client := pb.NewJinaExecutorSnapshotClient(conn)
//     response, err := client.Snapshot(context.Background(), &emptypb.Empty{})
//     if err != nil {
//         log.Printf("Error triggering a snapshot: %v", err)
//         return nil, err
//     }
//
//     snapshot := &snapshot{
//         executor:          fsm.executor,
//         id:                response.Id,
//         status:            &response.Status,
//         snapshotFile:      response.SnapshotFile,
//     }
//     fsm.snapshot = snapshot
//
//     return snapshot, nil
}

func (fsm *executorFSM) Restore(r io.ReadCloser) error {
    // I think restore here is not well set
    log.Printf("executorFSM method Restore")
    return nil
//     bytes, err := io.ReadAll(r)
//     // write bytes to temporary file, and pass it in the request
//     if err != nil {
//         log.Printf("Error reading bytes from the snapshot file %v", err)
//         return err
//     }
//     tempDir := os.TempDir()
//     file, err := ioutil.TempFile(tempDir, "temp")
//     if err != nil {
//         log.Print(err)
//     }
//     defer os.Remove(file.Name()) // remove the file when done
//
//     log.Printf("Temporary file name %s", file.Name())
//
//     // Write some data to the file
//     if _, err := file.Write(bytes); err != nil {
//         log.Printf("Error writing snapshot bytes to temporary file %v", err)
//         return err
//     }
//
//     // Close the file
//     if err := file.Close(); err != nil {
//         log.Printf("Error closing file", err)
//         return err
//     }
//     log.Printf("calling underlying executor")
//     conn, err := fsm.executor.newConnection()
//     if err != nil {
//         return err
//     }
//     defer conn.Close()
//     client := pb.NewJinaExecutorRestoreClient(conn)
//     restoreCommandProto := &pb.RestoreSnapshotCommand{}
//     restoreCommandProto.SnapshotFile = file.Name()
//     restoreResponse, err := client.Restore(context.Background(), restoreCommandProto)
//     if err != nil {
//         log.Printf("Restore command issues to Executor failed %v", err)
//         return err
//     }
//     log.Printf("Start Checking status of Restore")
//     ticker := time.NewTicker(1 * time.Second)
//     done := make(chan bool)
//     defer close(done)
//     timeout := time.NewTimer(500 * time.Second)
//
//     go func(funcTicker *time.Ticker) {
//         for {
//             select {
//             case t := <-funcTicker.C:
//                 log.Printf("Checking restore status at ", t)
//                 conn, err = fsm.executor.newConnection()
//                 if err == nil {
//                     defer conn.Close()
//                     client := pb.NewJinaExecutorRestoreProgressClient(conn)
//                     response, err := client.RestoreStatus(context.Background(), restoreResponse.Id)
//                     if err != nil {
//                         log.Printf("error fetching restore status for id: %s", restoreResponse.Id)
//                     } else {
//
//                         log.Printf("Restore status at time %v is %s", t, response.Status)
//                         if response.Status == pb.RestoreSnapshotStatusProto_FAILED ||
//                             response.Status == pb.RestoreSnapshotStatusProto_SUCCEEDED {
//                             if response.Status == pb.RestoreSnapshotStatusProto_FAILED {
//                                  err = errors.New("Restoring Executor failed")
//                             }
//                             timeout.Stop()
//                             done <- true
//                             return
//                         }
//                     }
//                 }
//             case <-timeout.C:
//                 log.Printf("Timed out waiting for restore status.")
//                 timeout.Stop()
//                 done <- true
//                 return
//             }
//         }
//     }(ticker)
//     <-done
//     ticker.Stop()
//     return err
}

func (fsm *executorFSM) Read(bytes []byte) (*pb.DataRequestProto, error) {
    log.Printf("executorFSM call Read endpoint")
    fsm.mtx.Lock()
    // TODO: Learn how to extract l.data and pass bytes to Python and back, in Python load DataRequest from those bytes and also here
    defer fsm.mtx.Unlock()
    cstr := (*C.char)(unsafe.Pointer(&bytes[0]))

    pyBytes := C.PyBytes_FromStringAndSize(cstr, C.long(len(bytes)))
    ret := C.call_handle_binary_request(fsm.handle_binary_request_func, fsm.executor, pyBytes)
    var go_bytes []byte
    c_bytes := C.PyBytes_AsString(ret)
    length := C.PyBytes_Size(ret)
    header := (*reflect.SliceHeader)(unsafe.Pointer(&go_bytes))
    header.Data = uintptr(unsafe.Pointer(c_bytes))
    header.Len = int(length)
    header.Cap = int(length)
    response := &pb.DataRequestProto{}
    err := proto.Unmarshal(go_bytes, response)
    if err != nil {
        log.Printf("EROR UNMARSHALLING RESPONSE FROM PYTHON: %v", err)
        return nil, err
    }
    return response, nil
//     conn, err := fsm.executor.newConnection()
//     if err != nil {
//         return nil, err
//     }
//     defer conn.Close()
//     client := pb.NewJinaSingleDataRequestRPCClient(conn)
//     response, err := client.ProcessSingleData(ctx, dataRequestProto)
//     if err != nil {
//         log.Printf("Error calling read endpoint: %v", err)
//         return nil, err
//     }
//
//     return response, err
}

func (fsm *executorFSM) EndpointDiscovery(ctx context.Context, empty *empty.Empty) (*pb.EndpointsProto, error) {
    err := errors.New("Temporary errror")
    log.Printf("executorFSM call EndpointDiscovery")
    return nil, err
//     conn, err := fsm.executor.newConnection()
//     if err != nil {
//         return nil, err
//     }
//     defer conn.Close()
//     client := pb.NewJinaDiscoverEndpointsRPCClient(conn)
//     response, err := client.EndpointDiscovery(ctx, empty)
//     if err != nil {
//         log.Printf("Error calling EndpointDiscovery endpoint: %v", err)
//         return nil, err
//     }
//
//     return response, err
}


func (fsm *executorFSM) XStatus(ctx context.Context, empty *empty.Empty) (*pb.JinaInfoProto, error) {
    log.Printf("executorFSM call Status")
    return nil, nil
//     conn, err := fsm.executor.newConnection()
//     if err != nil {
//         return nil, err
//     }
//     defer conn.Close()
//     client := pb.NewJinaInfoRPCClient(conn)
//     response, err := client.XStatus(ctx, empty)
//     if err != nil {
//         log.Printf("Error calling Status endpoint: %v", err)
//         return nil, err
//     }
//
//     return response, err
}

