import jraft

address = "localhost:50051"
raftId = "nodeA"
raftDir = "/tmp/jina-raft-cluster"
raftBootstrap = False
executorTarget = "localhost:60061"

args = [address, raftId, raftDir, raftBootstrap, executorTarget]
jraft.run(*args)
