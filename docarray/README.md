# DocArray

<p align="center">
<b>The universal data type for neural search</b>
</p>

<p align=center>
<a href="https://pypi.org/project/docarray/"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8 3.9" title="DocArray requires Python 3.7 and above"></a>
<a href="https://pypi.org/project/docarray/"><img src="https://img.shields.io/pypi/v/docarray?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
</p>



## Install

```bash
pip install -U docarray
```

Jina already contains the latest `docarray`. If you have installed `jina`, then there is no need to install `docarray` again. 


## [Documentation](https://docs.jina.ai/fundamentals/document/)

All APIs can be used, just change the namespace:

```diff
- from jina import Document, DocumentArray
+ from docarray import Document, DocumentArray

d = Document()
da = DocumentArray.empty(10)
```
