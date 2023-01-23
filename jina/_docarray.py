try:
    from docarray import BaseDocument, DocumentArray
    from docarray.documents.legacy import Document
except ImportError:
    from docarray import Document, DocumentArray

    BaseDocument = Document
