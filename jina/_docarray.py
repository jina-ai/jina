try:
    from docarray import BaseDoc as Document
    from docarray import DocList as DocumentArray

    docarray_v2 = True

except ImportError:
    from docarray import Document, DocumentArray

    docarray_v2 = False
