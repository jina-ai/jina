try:
    from docarray import BaseDocument, DocumentArray
    from docarray.documents.legacy import Document
    from docarray.documents.legacy import DocumentArray as LegacyDocumentArray

    docarray_v2 = True

except ImportError:
    from docarray import Document, DocumentArray

    BaseDocument = Document
    LegacyDocumentArray = DocumentArray
    docarray_v2 = False
