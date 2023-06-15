package main

import (
    "context"
    "os"
    "errors"

    pb "github.com/Jille/raftadmin/proto"
    "google.golang.org/grpc"
    "google.golang.org/protobuf/encoding/prototext"
    "google.golang.org/protobuf/reflect/protoreflect"
    hclog "github.com/hashicorp/go-hclog"
)

func AddVoter(target string, id string, voter_address string) error {
    logLevel := os.Getenv("JINA_LOG_LEVEL")
    if logLevel == "" {
        logLevel = "INFO"
    }
    add_voter_logger := hclog.New(&hclog.LoggerOptions{
                    Name:  "add_voter-" + id,
                    Level: hclog.LevelFromString(logLevel),
                })
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
        add_voter_logger.Error("Error dialing:", "error", err)
        return err
    }
    defer conn.Close()

    add_voter_logger.Debug("Invoking", "method", m.Name(), "with request", prototext.Format(req))
    futurereq := &pb.Future{}
    resp := futurereq.ProtoReflect().New().Interface()
    if err := conn.Invoke(ctx, "/RaftAdmin/" + string(m.Name()), req, resp); err != nil {
        add_voter_logger.Error("Error invoking", "error", err)
        return err
    }

    // This method returned a future. We should call Await to get the result, and then Forget to free up the memory of the server.
    if f, ok := resp.(*pb.Future); ok {
        c := pb.NewRaftAdminClient(conn)
        add_voter_logger.Debug("Awaiting for response")
        resp, err := c.Await(ctx, f)
        add_voter_logger.Debug("Response from AddVoter:", "Response", prototext.Format(resp))

        if resp.Error != "" {
            // handle error
            add_voter_logger.Error("Error in AddVoter Response:", "error", resp.Error)
            return errors.New("Error in AddVoter Response: target is not the leader")
        }
        if err != nil {
            add_voter_logger.Error("Error from AddVoter:", "error", err)
            return err
        }
        if _, err := c.Forget(ctx, f); err != nil {
            add_voter_logger.Error("Returning error", "error", err)
            return err
        }
    }
    return nil
}
