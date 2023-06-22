package main

/*

#cgo pkg-config: python3
#include <Python.h>
#include <stdbool.h>

// Workaround missing variadic function support
// https://github.com/golang/go/issues/975
int PyArg_ParseTuple_run(PyObject * args, PyObject * kwargs, char **myAddr, char **raftId, char **raftDir, char **executorTarget, int *HeartbeatTimeout, int *ElectionTimeout, int *CommitTimeout, int *MaxAppendEntries, bool *BatchApplyCh, bool *ShutdownOnRemove, uint64_t *TrailingLogs, int *snapshotInterval, uint64_t *SnapshotThreshold, int *LeaderLeaseTimeout, char **LogLevel, bool *NoSnapshotRestoreOnStart) {
    static char *kwlist[] = {"myAddr", "raftId", "raftDir", "executorTarget", "HeartbeatTimeout", "ElectionTimeout", "CommitTimeout", "MaxAppendEntries", "BatchApplyCh", "ShutdownOnRemove", "TrailingLogs", "SnapshotInterval", "SnapshotThreshold", "LeaderLeaseTimeout", "LogLevel", "NoSnapshotRestoreOnStart", NULL};
    return PyArg_ParseTupleAndKeywords(args, kwargs, "ssss|llllppklklsp", kwlist, myAddr, raftId, raftDir, executorTarget, HeartbeatTimeout, ElectionTimeout, CommitTimeout, MaxAppendEntries, BatchApplyCh, ShutdownOnRemove, TrailingLogs, snapshotInterval, SnapshotThreshold, LeaderLeaseTimeout, LogLevel, NoSnapshotRestoreOnStart);
}

int PyArg_ParseTuple_add_voter(PyObject * args, char **a, char **b, char **c) {
    return PyArg_ParseTuple(args, "sss", a, b, c);
}

int PyArg_ParseTuple_get_configuration(PyObject * args, char **a, char **b) {
    return PyArg_ParseTuple(args, "ss", a, b);
}

PyObject * run(PyObject* , PyObject*, PyObject*);

PyObject * add_voter(PyObject* , PyObject*);
PyObject * get_configuration(PyObject* , PyObject*);

static PyMethodDef methods[] = {
    {"run", (PyCFunction)run, METH_VARARGS | METH_KEYWORDS, "Run the raft Node server"},
    {"add_voter", (PyCFunction)add_voter, METH_VARARGS, "Client to add voter"},
    {"get_configuration", (PyCFunction)get_configuration, METH_VARARGS, "Get configuration"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef jraftmodule = {
   PyModuleDef_HEAD_INIT, "jraft", NULL, -1, methods
};

PyMODINIT_FUNC
PyInit_jraft(void)
{
    PyObject *m;
    m = PyModule_Create(&jraftmodule);
    if (m == NULL)
        return NULL;
    return m;
}

void raise_exception(char *msg) {
    PyErr_SetString(PyExc_ValueError, msg);
}

*/
import "C"


