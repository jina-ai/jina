# Jina

![Build Docker Status Badge](https://github.com/jina-ai/jina/workflows/Build%20Docker/badge.svg)
![Unit Test Status Badge](https://github.com/jina-ai/jina/workflows/Unit%20Test/badge.svg)

Jina is *the* cloud-native semantic search solution powered by SOTA AI technology.


## Getting Started

The simplest way to run Jina is via the docker container. 

### Run with docker image

```bash
docker login -u USERNAME -p TOKEN docker.pkg.github.com
docker run docker.pkg.github.com/jina-ai/jina/jina:master-debian
```

This command downloads the latest Jina image and runs it in a container. When the container runs, it prints an help message and exits.


If you want to run Jina without Docker, please make sure you have Python 3.7 installed. 
If you are using `pyenv` for controlling the Python virtual environment, make sure the Jina codebase is covered by `pyenv local 3.7.x`

### Install from PyPi
 
```bash
pip install jina
jina --help
```

### Install from this Git repository

```bash
pip install git+https://github.com/jina-ai/jina.git
jina --help
```

### (Dev mode) Install from your local folk/clone 

For developers who want to edit the project’s code and test the changes on-the-fly, 

```bash
git clone https://github.com/jina-ai/jina
cd jina && pip install -e .
jina --help
``` 
  
  
## Documentation 

To build the documentation locally, you need to have Docker installed. Clone this repository and run the following command: 
```bash
bash ./make-doc.sh 8080
```

The documentation is now available at `http://0.0.0.0:8080/`.  Removing `8080` from the arguments if you do not want to view generated docs in the browser. 

## License

If you have downloaded a copy of the GNES binary or source code, please note that Jina's binary and source code are both licensed under the [Apache 2.0](LICENSE).
