try:
    from docarray import BaseDocument as Document
    from docarray import DocumentArray

    docarray_v2 = True

except ImportError:
    from docarray import Document, DocumentArray

    docarray_v2 = False
