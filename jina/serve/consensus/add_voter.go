package main

import (
    "context"
    "log"

    pb "github.com/Jille/raftadmin/proto"
    "google.golang.org/grpc"
    "google.golang.org/protobuf/encoding/prototext"
    "google.golang.org/protobuf/reflect/protoreflect"
)

func AddVoter(target string, id string, voter_address string) error {
    ctx := context.Background()
    m := pb.File_raftadmin_proto.Services().ByName("RaftAdmin").Methods().ByName("AddVoter")
    // Sort fields by field number.
    reqDesc := m.Input()
    unorderedFields := reqDesc.Fields()
    fields := make([]protoreflect.FieldDescriptor, unorderedFields.Len())

    for i := 0; unorderedFields.Len() > i; i++ {
        f := unorderedFields.Get(i)
        fields[f.Number()-1] = f
    }
    req := &pb.AddVoterRequest {
                  Id: id,
                  Address: voter_address,
                  PreviousIndex: 0,
              }

    // Connect and send the RPC.
    var o grpc.DialOption = grpc.EmptyDialOption{}
    conn, err := grpc.Dial(target, grpc.WithInsecure(), grpc.WithBlock(), o)
    if err != nil {
        return err
    }
    defer conn.Close()

    log.Printf("Invoking %s(%s)", m.Name(), prototext.Format(req))
    futurereq := &pb.Future{}
    resp := futurereq.ProtoReflect().New().Interface()
    log.Printf("resp %v", resp)
    if err := conn.Invoke(ctx, "/RaftAdmin/"+string(m.Name()), req, resp); err != nil {
        return err
    }
    log.Printf("Response: %s", prototext.Format(resp))

    // This method returned a future. We should call Await to get the result, and then Forget to free up the memory of the server.
    if f, ok := resp.(*pb.Future); ok {
        c := pb.NewRaftAdminClient(conn)
        log.Printf("Invoking Await(%s)", prototext.Format(f))
        resp, err := c.Await(ctx, f)
        if err != nil {
            return err
        }
        log.Printf("Response: %s", prototext.Format(resp))
        if _, err := c.Forget(ctx, f); err != nil {
            return err
        }
    }
    return nil
}