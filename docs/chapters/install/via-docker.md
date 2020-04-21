# Install Jina via Docker Container

The simplest way to use Jina is via Docker. We provide a universal container image as small as 100MB that can be run on multiple architectures without worry about package dependencies. Of course, you need to have [Docker installed](https://docs.docker.com/install/) first. 

## Running Jina Image

```bash
docker run jinaai/jina
```

This command downloads the latest Jina image from [Docker Hub](https://hub.docker.com/r/jinaai/jina/tags) based on your local architecture and then runs it in a container. When the container runs, it prints an help message and exits.

### Supported Architectures

This Docker image is based on `python:3.7.6-slim` and can be run on the following CPU architectures: 

- amd64
- arm64
- ppc64le
- s390x
- 386
- arm/v7
- arm/v6

No extra steps is required to run on those architectures, simply do `docker run jinaai/jina`
