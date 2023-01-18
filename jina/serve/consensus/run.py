import multiprocessing
import time

#./jraft --raft_bootstrap --raft_id=nodeA --address=localhost:50051 --executor_target=localhost:60061 --raft_data_dir /tmp/jina-raft-cluster
# raft_bootstrap = True
# raft_id = '0'
# address = 'localhost:50051'
# executor_target = 'localhost:60061'
# raft_data_dir = '/tmp/jina-raft-cluster'



#localhost:49515, 2, /home/joan/jina/jina/toy_workspace, %!p(bool=false), localhost:49516
def a():
    import jraft

    raft_bootstrap = False
    raft_id = '2'
    address = 'localhost:49515'
    executor_target = 'localhost:49516'
    raft_data_dir = '/home/joan/jina/jina/toy_workspace'
    jraft.run(address, raft_id, raft_data_dir, raft_bootstrap, executor_target)

process = multiprocessing.Process(target=a, daemon=True)
process.start()
time.sleep(5)
process.kill()
time.sleep(2)
a()