## Pre-requisites

In this tutorial, we will need the following dependencies installed:
```shell
pip install Pillow jina==2.1.13 torch==1.9.0 torchvision==0.10.0 transformers==4.9.1 yolov5==5.0.7 lmdb==1.2.1 matplotlib jina-commons@git+https://github.com/jina-ai/jina-commons.git#egg=jina-commons
```

We also need to download [the dataset](https://open-images.s3.eu-central-1.amazonaws.com/data.zip) and unzip it.

You can use the link or the following commands:
```shell
wget https://open-images.s3.eu-central-1.amazonaws.com/data.zip
unzip data.zip
```

You should find 2 folders after unzipping:
* images: this folder contains the images that we will index
* query: this folder contains small images that we will use as search queries
