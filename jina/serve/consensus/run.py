import ctypes
go_lib = ctypes.CDLL("./libjinaraft.so")
run = go_lib.RunC
run.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_bool, ctypes.c_char_p]

address = "localhost:50051"
raftId = "nodeA"
raftDir = "/tmp/jina-raft-cluster"
raftBootstrap = False
executorTarget = "localhost:60061"

try:
    run(address.encode(), raftId.encode(), raftDir.encode(), raftBootstrap, executorTarget.encode())
except KeyboardInterrupt:
    pass

