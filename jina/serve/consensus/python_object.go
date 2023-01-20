package main
//
// import "fmt"
//
// /*
// #include <Python.h>
//
// static PyObject* call_python_function(const char* module_name, const char* function_name) {
//     PyObject* function;
//     PyObject* args;
//     PyObject* result;
//     PyObject* module;
//     //Py_Initialize();
//     module = PyImport_ImportModule(module_name);
//     if (module == NULL) {
//         printf("Failed to import module");
//         return NULL;
//     }
//     function = PyObject_GetAttrString(module, function_name);
//     args = PyTuple_New(0);
//     result = PyObject_CallObject(function, args);
//     //Py_Finalize();
//     return result;
// }
// */
// import "C"
//
// //CGO_CFLAGS=-I/usr/include/python3.7m CGO_LDFLAGS="-lpython3.7m" go build python_object.go
// //PYTHONPATH='.' ./python_object
// func main() {
//     C.Py_Initialize()
//     defer C.Py_Finalize()
//
//     pyObject := C.call_python_function(C.CString("module_name"), C.CString("create_worker_request_handler"))
//     if pyObject == nil {
//         fmt.Println("Failed to get PyObject")
//         return
//     }
//     fmt.Println("REFERENCE COUNT OF OBJECT %v", pyObject.ob_refcnt)
//
//     pyMethod := C.PyObject_GetAttrString(pyObject, C.CString("print"))
//
//     if pyMethod == nil {
//         if C.PyErr_Occurred() != nil {
//             C.PyErr_Print()
//         }
//         fmt.Println("Failed to get PyMethod")
//         return
//     }
//     args := C.PyTuple_New(0);
//     C.PyObject_CallObject(pyMethod, args);
// }
