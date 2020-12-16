import random
import string

import numpy as np

from jina import Document


def text_document_generator(num_docs):
    for i in range(num_docs):
        length = random.randint()
        document = Document(text=''.join(random.choices(string.ascii_uppercase + string.digits, k=length)))
        yield document


def image_document_generator(num_docs):
    length = random.randint()
    height = random.randint()
    for i in range(num_docs):
        document = Document(blob=np.random.rand(height, length, 3))
        yield document


def multimodal_document_generator(num_docs):
    length = random.randint()
    height = random.randint()
    for i in range(num_docs):
        document = Document(blob=np.random.rand(height, length, 3))
        yield document
