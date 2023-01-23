try:
    from docarray import BaseDocument, DocumentArray
    from docarray.documents.legacy import Document
    from docarray.documents.legacy import DocumentArray as LegacyDocumentArray

except ImportError:
    from docarray import Document, DocumentArray

    BaseDocument = Document
    LegacyDocumentArray = DocumentArray
