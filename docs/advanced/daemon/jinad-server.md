(jinad-server)=
# JinaD Server

`JinaD` docker image is published
on [Docker Hub](https://hub.docker.com/r/jinaai/jina/tags?page=1&ordering=last_updated&name=-daemon) and follows
the [standard image versioning](https://github.com/jina-ai/jina/blob/master/RELEASE.md#docker-image-versioning) used in
Jina.

## Run

To deploy JinaD, SSH into a remote instance (e.g.- ec2 instance) and run the below command.

```bash
docker run --add-host host.docker.internal:host-gateway \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v /tmp/jinad:/tmp/jinad \
           -p 8000:8000 \
           --name jinad \
           -d jinaai/jina:master-daemon
```

````{admonition} Note
:class: note
You can change the port via the `-p` argument. Following code assumes that `HOST` is the public IP of the above
instance and `PORT` is as passed in the docker run cpmmand.
````

````{admonition} Important
:class: important
`JinaD` should always be deployed as a docker container. Simply starting the server using `jinad` command would not
work.
````

## API docs

- [Static docs with redoc](https://api.jina.ai/daemon/)

- [Interactive swagger docs](http://localhost:8000/docs) (works once JinaD is started)
