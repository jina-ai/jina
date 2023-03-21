package main

// #include <Python.h>
// #include <stdbool.h>
// int PyArg_ParseTuple_run(PyObject * args, PyObject * kwargs, char **myAddr, char **raftId, char **raftDir, char **executorTarget, int *HeartbeatTimeout, int *ElectionTimeout, int *CommitTimeout, int *MaxAppendEntries, bool *BatchApplyCh, bool *ShutdownOnRemove, uint64_t *TrailingLogs, int *snapshotInterval, uint64_t *SnapshotThreshold, int *LeaderLeaseTimeout, char **LogLevel, bool *NoSnapshotRestoreOnStart);
// int PyArg_ParseTuple_add_voter(PyObject * args, char **a, char **b, char **c);
// int PyArg_ParseTuple_get_configuration(PyObject * args, char **a, char **b);
// void raise_exception(char *msg);
import "C"


import (
    "context"
    "flag"
    "fmt"
    "log"
    "net"
    "os"
    "os/signal"
    "syscall"
    "path/filepath"
    "time"
    "unsafe"

    // "github.com/Jille/raft-grpc-leader-rpc/leaderhealth"
    transport "github.com/Jille/raft-grpc-transport"
    "github.com/Jille/raftadmin"
    "github.com/hashicorp/raft"
    boltdb "github.com/hashicorp/raft-boltdb"
    jinaraft "jraft/jina_raft"
    pb "jraft/jina-go-proto"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    "google.golang.org/grpc/reflection"
    healthpb "google.golang.org/grpc/health/grpc_health_v1"
)

func NewRaft(ctx context.Context,
            myID string,
            myAddress string,
            raftDir string,
            HeartbeatTimeout int,
            ElectionTimeout int,
            CommitTimeout int,
            MaxAppendEntries int,
            BatchApplyCh bool,
            ShutdownOnRemove bool,
            TrailingLogs uint64,
            SnapshotInterval int,
            SnapshotThreshold uint64,
            LeaderLeaseTimeout int,
            LogLevel string,
            NoSnapshotRestoreOnStart bool,
            fsm raft.FSM) (*raft.Raft, *transport.Manager, error) {

    config := raft.DefaultConfig()
    config.LocalID = raft.ServerID(myID)
    config.HeartbeatTimeout         = time.Duration(HeartbeatTimeout) * time.Millisecond
    config.ElectionTimeout          = time.Duration(ElectionTimeout) * time.Millisecond
    config.CommitTimeout            = time.Duration(CommitTimeout) * time.Millisecond
    config.MaxAppendEntries         = MaxAppendEntries
    config.BatchApplyCh             = BatchApplyCh
    config.ShutdownOnRemove         = ShutdownOnRemove
    config.TrailingLogs             = TrailingLogs
    config.SnapshotInterval         = time.Duration(SnapshotInterval) * time.Second
    config.SnapshotThreshold        = SnapshotThreshold
    config.LeaderLeaseTimeout       = time.Duration(LeaderLeaseTimeout) * time.Millisecond
    config.LogLevel                 = LogLevel
    config.NoSnapshotRestoreOnStart = NoSnapshotRestoreOnStart

    baseDir := filepath.Join(raftDir, myID)
    err := os.MkdirAll(baseDir, os.ModePerm)
    if err != nil {
        fmt.Printf("Error creating baseDir (%v) folder: %v\n", baseDir, err)
    }

    logs_db, err := boltdb.NewBoltStore(filepath.Join(baseDir, "logs.dat"))
    if err != nil {
        return nil, nil, fmt.Errorf(`boltdb.NewBoltStore(%q): %v`, filepath.Join(baseDir, "logs.dat"), err)
    }

    stable_db, err := boltdb.NewBoltStore(filepath.Join(baseDir, "stable.dat"))
    if err != nil {
        return nil, nil, fmt.Errorf(`boltdb.NewBoltStore(%q): %v`, filepath.Join(baseDir, "stable.dat"), err)
    }

    file_snapshot, err := raft.NewFileSnapshotStore(baseDir, 3, os.Stderr)
    if err != nil {
        return nil, nil, fmt.Errorf(`raft.NewFileSnapshotStore(%q, ...): %v`, baseDir, err)
    }

    tm := transport.New(raft.ServerAddress(myAddress), []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())})

    r, err := raft.NewRaft(config, fsm, logs_db, stable_db, file_snapshot, tm.Transport())

    if err != nil {
        return nil, nil, fmt.Errorf("raft.NewRaft: %v", err)
    }

    cfg := raft.Configuration{
        Servers: []raft.Server{
            {
                Suffrage: raft.Voter,
                ID:       raft.ServerID(myID),
                Address:  raft.ServerAddress(myAddress),
            },
        },
    }
    f := r.BootstrapCluster(cfg)
    // raft bootstrap error can be ignored safely https://github.com/hashicorp/raft/blob/44124c28758b8cfb675e90c75a204a08a84f8d4f/api.go#L220
    if err := f.Error(); err != nil {
        log.Printf("raft.Raft.BootstrapCluster: %v, raft cluster already bootstrapped", err)
        return r, tm, nil
    }

    return r, tm, nil
}

func Run(myAddr string,
         raftId string,
         raftDir string,
         executorTarget string,
         HeartbeatTimeout int,
         ElectionTimeout int,
         CommitTimeout int,
         MaxAppendEntries int,
         BatchApplyCh bool,
         ShutdownOnRemove bool,
         TrailingLogs uint64,
         SnapshotInterval int,
         SnapshotThreshold uint64,
         LeaderLeaseTimeout int,
         LogLevel string,
         NoSnapshotRestoreOnStart bool) {

    log.Printf("Calling Run %s, %s, %s, %s", myAddr, raftId, raftDir, executorTarget)
    if raftId == "" {
        log.Fatalf("flag --raft_id is required")
    }

    ctx := context.Background()
    _, port, err := net.SplitHostPort(myAddr)
    if err != nil {
        log.Fatalf("failed to parse local address (%q): %v", myAddr, err)
    }
    log.Printf("starting to listen on port %s", port)
    sock, err := net.Listen("tcp", fmt.Sprintf(":%s", port))
    if err != nil {
        log.Fatalf("failed to listen: %v", err)
    }
    executorFSM := jinaraft.NewExecutorFSM(executorTarget)

    r, tm, err := NewRaft(ctx,
                        raftId,
                        myAddr,
                        raftDir,
                        HeartbeatTimeout,
                        ElectionTimeout,
                        CommitTimeout,
                        MaxAppendEntries,
                        BatchApplyCh,
                        ShutdownOnRemove,
                        TrailingLogs,
                        SnapshotInterval,
                        SnapshotThreshold,
                        LeaderLeaseTimeout,
                        LogLevel,
                        NoSnapshotRestoreOnStart,
                        executorFSM)
    if err != nil {
        log.Fatalf("failed to start raft: %v", err)
    }
    grpcServer := grpc.NewServer()
    pb.RegisterJinaSingleDataRequestRPCServer(grpcServer, &jinaraft.RpcInterface{
        Executor: executorFSM,
        Raft:     r,
    })
    pb.RegisterJinaDiscoverEndpointsRPCServer(grpcServer, &jinaraft.RpcInterface{
        Executor: executorFSM,
        Raft:     r,
    })
    pb.RegisterJinaInfoRPCServer(grpcServer, &jinaraft.RpcInterface{
        Executor: executorFSM,
        Raft:     r,
    })
    tm.Register(grpcServer)
    //leaderhealth.Setup(r, grpcServer, []string{"Health"})

    //healthpb.RegisterHealthServer(grpcServer, health.NewServer())
    healthpb.RegisterHealthServer(grpcServer, &jinaraft.RpcInterface{
        Executor: executorFSM,
        Raft:     r,
    })


    raftadmin.Register(grpcServer, r)
    reflection.Register(grpcServer)
    sigchnl := make(chan os.Signal, 1)
    signal.Notify(sigchnl, syscall.SIGINT, syscall.SIGTERM)
    go func(){
        sig := <-sigchnl
        log.Printf("Signal %v received", sig)
        grpcServer.Stop()
        shutdownResult := r.Shutdown()
        err := shutdownResult.Error()
        if err != nil {
            log.Fatalf("Error returned while shutting RAFT down: %v", err)
        }
        os.Exit(0)
    }()
    if err := grpcServer.Serve(sock); err != nil {
        log.Fatalf("failed to serve: %v", err)
    }
}

func findServerByID(servers []raft.Server, id raft.ServerID) *raft.Server {
	for _, server := range servers {
		if server.ID == id {
			return &server
		}
	}
	return nil
}

func main() {
    raftDefaultConfig := raft.DefaultConfig()

    myAddr                   := flag.String("address", "localhost:50051", "TCP host+port for this node")
    raftId                   := flag.String("raft_id", "", "Node id used by Raft")
    raftDir                  := flag.String("raft_data_dir", "data/", "Raft data dir")
    executorTarget           := flag.String("executor_target", "localhost:54321", "underlying executor host+port")
    HeartbeatTimeout         := flag.Int("heartbeat_timeout", int(raftDefaultConfig.HeartbeatTimeout / time.Millisecond), "HeartbeatTimeout for the RAFT node")
    ElectionTimeout          := flag.Int("election_timeout", int(raftDefaultConfig.ElectionTimeout / time.Millisecond), "ElectionTimeout for the RAFT node")
    CommitTimeout            := flag.Int("commit_timeout", int(raftDefaultConfig.CommitTimeout / time.Millisecond), "CommitTimeout for the RAFT node")
    MaxAppendEntries         := flag.Int("max_append_entries", raftDefaultConfig.MaxAppendEntries, "MaxAppendEntries for the RAFT node")
    BatchApplyCh             := flag.Bool("batch_applych", raftDefaultConfig.BatchApplyCh, "BatchApplyCh for the RAFT node")
    ShutdownOnRemove         := flag.Bool("shutdown_on_remove", raftDefaultConfig.ShutdownOnRemove, "ShutdownOnRemove for the RAFT node")
    TrailingLogs             := flag.Uint64("trailing_logs", raftDefaultConfig.TrailingLogs, "TrailingLogs for the RAFT node")
    SnapshotInterval         := flag.Int("snapshot_interval", int(raftDefaultConfig.SnapshotInterval / time.Second), "SnapshotInterval for the RAFT node")
    SnapshotThreshold        := flag.Uint64("snapshot_threshold", raftDefaultConfig.SnapshotThreshold, "SnapshotThreshold for the RAFT node")
    LeaderLeaseTimeout       := flag.Int("leader_lease_timeout", int(raftDefaultConfig.LeaderLeaseTimeout / time.Millisecond), "LeaderLeaseTimeout for the RAFT node")
    LogLevel                 := flag.String("log_level", raftDefaultConfig.LogLevel, "LogLevel for the RAFT node")
    NoSnapshotRestoreOnStart := flag.Bool("no_snapshot_restore_on_start", raftDefaultConfig.NoSnapshotRestoreOnStart, "NoSnapshotRestoreOnStart for the RAFT node")

    Run(*myAddr,
        *raftId,
        *raftDir,
        *executorTarget,
        *HeartbeatTimeout,
        *ElectionTimeout,
        *CommitTimeout,
        *MaxAppendEntries,
        *BatchApplyCh,
        *ShutdownOnRemove,
        *TrailingLogs,
        *SnapshotInterval,
        *SnapshotThreshold,
        *LeaderLeaseTimeout,
        *LogLevel,
        *NoSnapshotRestoreOnStart)
}


//export run
func run(self *C.PyObject, args *C.PyObject, kwargs *C.PyObject) *C.PyObject {
    var myAddr *C.char
    var raftId *C.char
    var raftDir *C.char
    var executorTarget *C.char
    var HeartbeatTimeout C.int
    var ElectionTimeout C.int
    var CommitTimeout C.int
    var MaxAppendEntries C.int
    var BatchApplyCh C.bool
    var ShutdownOnRemove C.bool
    var TrailingLogs C.uint64_t
    var SnapshotInterval C.int
    var SnapshotThreshold C.uint64_t
    var LeaderLeaseTimeout C.int
    var LogLevel *C.char
    var NoSnapshotRestoreOnStart C.bool

    raftDefaultConfig := raft.DefaultConfig()
    HeartbeatTimeout         = C.int(int64(raftDefaultConfig.HeartbeatTimeout / time.Millisecond))
    ElectionTimeout          = C.int(int64(raftDefaultConfig.ElectionTimeout / time.Millisecond))
    CommitTimeout            = C.int(int64(raftDefaultConfig.CommitTimeout / time.Millisecond))
    MaxAppendEntries         = C.int(raftDefaultConfig.MaxAppendEntries)
    BatchApplyCh             = C.bool(raftDefaultConfig.BatchApplyCh)
    ShutdownOnRemove         = C.bool(raftDefaultConfig.ShutdownOnRemove)
    TrailingLogs             = C.uint64_t(raftDefaultConfig.TrailingLogs)
    SnapshotInterval         = C.int(raftDefaultConfig.SnapshotInterval / time.Second)
    SnapshotThreshold        = C.uint64_t(raftDefaultConfig.SnapshotThreshold)
    LeaderLeaseTimeout       = C.int(raftDefaultConfig.LeaderLeaseTimeout / time.Millisecond)
    LogLevel                 = C.CString(raftDefaultConfig.LogLevel)
    NoSnapshotRestoreOnStart = C.bool(raftDefaultConfig.NoSnapshotRestoreOnStart)

    if C.PyArg_ParseTuple_run(args,
                             kwargs,
                             &myAddr,
                             &raftId,
                             &raftDir,
                             &executorTarget,
                             &HeartbeatTimeout,
                             &ElectionTimeout,
                             &CommitTimeout,
                             &MaxAppendEntries,
                             &BatchApplyCh,
                             &ShutdownOnRemove,
                             &TrailingLogs,
                             &SnapshotInterval,
                             &SnapshotThreshold,
                             &LeaderLeaseTimeout,
                             &LogLevel,
                             &NoSnapshotRestoreOnStart) != 0 {
        Run(C.GoString(myAddr),
            C.GoString(raftId),
            C.GoString(raftDir),
            C.GoString(executorTarget),
            int(HeartbeatTimeout),
            int(ElectionTimeout),
            int(CommitTimeout),
            int(MaxAppendEntries),
            BatchApplyCh != false,
            ShutdownOnRemove != false,
            uint64(TrailingLogs),
            int(SnapshotInterval),
            uint64(SnapshotThreshold),
            int(LeaderLeaseTimeout),
            C.GoString(LogLevel),
            NoSnapshotRestoreOnStart != false)
    }
    C.Py_IncRef(C.Py_None);
    return C.Py_None;
}

//export add_voter
func add_voter(self *C.PyObject, args *C.PyObject) *C.PyObject {
    var target *C.char
    var raftId *C.char
    var voterAddress *C.char
    if C.PyArg_ParseTuple_add_voter(args, &target, &raftId, &voterAddress) != 0 {
        err := AddVoter(C.GoString(target), C.GoString(raftId), C.GoString(voterAddress))
        if err != nil {
            log.Printf("Error received calling AddVoter %v, but return None", err)
            C.raise_exception(C.CString("Error from AddVoter"))
            return nil
        }
    }
    C.Py_IncRef(C.Py_None);
    return C.Py_None;
}

//export get_configuration
func get_configuration(self *C.PyObject, args *C.PyObject) *C.PyObject {

    var raftId *C.char
    var raftDir *C.char

    if C.PyArg_ParseTuple_get_configuration(args, &raftId, &raftDir) != 0 {
        config := raft.DefaultConfig()
        config.LocalID = raft.ServerID(C.GoString(raftId))

        baseDir := filepath.Join(C.GoString(raftDir), C.GoString(raftId))

        logs_db, err := boltdb.NewBoltStore(filepath.Join(baseDir, "logs.dat"))
        if logs_db != nil {
            defer logs_db.Close()
        }

        if err != nil {
            C.Py_IncRef(C.Py_None);
            return C.Py_None;
        }

        stable_db, err := boltdb.NewBoltStore(filepath.Join(baseDir, "stable.dat"))
        if stable_db != nil {
            defer stable_db.Close()
        }

        if err != nil {
            C.Py_IncRef(C.Py_None);
            return C.Py_None;
        }

        file_snapshot, err := raft.NewFileSnapshotStore(baseDir, 3, os.Stderr)
        if err != nil {
            C.Py_IncRef(C.Py_None);
            return C.Py_None;
        }

        // dummy transport
        tm := transport.New(raft.ServerAddress("0.0.0.0:54321"), []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())})

        // this will create a raft object, this is not really needed and we should find a work around so
        // we can get the configuration wihtout initializing anything else
        executorFSM := jinaraft.DummyExecutorFSM()

        conf, err := jinaraft.JinaGetConfiguration(config, executorFSM, logs_db, stable_db, file_snapshot, tm.Transport())
        if err != nil {
            C.Py_IncRef(C.Py_None);
            return C.Py_None;
        } else {
            fmt.Printf("configuration: %v\n", conf.Servers)
        }

        if len(conf.Servers) == 0 {
            C.Py_IncRef(C.Py_None);
            return C.Py_None;
        }


        server := findServerByID(conf.Servers, raft.ServerID(C.GoString(raftId)))
        cstr := C.CString(string(server.Address))
        defer C.free(unsafe.Pointer(cstr))
        pyStr := C.PyUnicode_FromString(cstr)
        return pyStr

    }
//     C.Py_IncRef(C.Py_None);
    C.raise_exception(C.CString("Error from get_configuration, wrong parameters passed"))
    return nil
}
