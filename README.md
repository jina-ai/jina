# _jina
Jina is the cloud-native semantic search solution powered by SOTA AI technology


## Prerequisites

Jina requires Python 3.7.


## Install

```bash
git clone https://github.com/jina-ai/_jina
cd _jina && pip install .
```

For developers who want to edit the project’s code and test the changes on-the-fly, please use `pip install -e .` 

If you are using `pyenv` to control the Python virtual environment, make sure the codebase is marked by `pyenv local 3.7.x`
  
  
## Documentation 

To build the document locally, you need to have Docker installed. Then simply run 
```bash
bash ./make-doc.sh 8080
```

The documentation is available at `http://0.0.0.0:8080/`. Simply remove `8080` from the arguments if you do not want to view generated docs in the browser. 

## Getting Started


