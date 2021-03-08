import pytest

from jina.enums import SocketType
from jina.executors import BaseExecutor
from jina.jaml import JAML


class MyExecutor(BaseExecutor):
    pass


def test_non_empty_reg_tags():
    assert JAML.registered_tags()
    assert 'BaseExecutor' in JAML.registered_tags()


@pytest.mark.parametrize(
    'include_unk, expected',
    [
        (
            True,
            '''
jtype: BaseExecutor {}
jtype: Blah {}
''',
        ),
        (
            False,
            '''
jtype: BaseExecutor {}
!Blah {}
''',
        ),
    ],
)
def test_include_unknown(include_unk, expected):
    y = '''
!BaseExecutor {}
!Blah {}
    '''
    assert JAML.escape(y, include_unknown_tags=include_unk).strip() == expected.strip()


@pytest.mark.parametrize(
    'original, escaped',
    [
        (
            '''
!BaseExecutor {}
!Blah {}
!MyExecutor {}
                                 ''',
            '''
jtype: BaseExecutor {}
!Blah {}
jtype: MyExecutor {}
                                 ''',
        ),
        (
            '''
!BaseExecutor
with:
    a: 123
    b: BaseExecutor
    jtype: unknown-blah
                                 ''',
            '''
jtype: BaseExecutor
with:
    a: 123
    b: BaseExecutor
    jtype: unknown-blah    
                                 ''',
        ),
        (
            '''
!CompoundIndexer
components:
  - !NumpyIndexer
    with:
      index_filename: vec.gz
      metric: euclidean
    metas:
      name: vecidx
  - !BinaryPbIndexer
    with:
      index_filename: doc.gz
    metas:
      name: docidx
metas:
  name: indexer
  workspace: $JINA_WORKSPACE

                                 ''',
            '''
jtype: CompoundIndexer
components:
  - jtype: NumpyIndexer
    with:
      index_filename: vec.gz
      metric: euclidean
    metas:
      name: vecidx
  - jtype: BinaryPbIndexer
    with:
      index_filename: doc.gz
    metas:
      name: docidx
metas:
  name: indexer
  workspace: $JINA_WORKSPACE
                                 ''',
        ),
        (
            '''
!CompoundIndexer
metas:
  workspace: $TMP_WORKSPACE
components:
  - !NumpyIndexer
    with:
      metric: euclidean
      index_filename: vec.gz
    metas:
      name: vecidx  # a customized name
  - !BinaryPbIndexer
    with:
      index_filename: chunk.gz
    metas:
      name: kvidx  # a customized name
requests:
  on:
    IndexRequest:
      - !VectorIndexDriver
        with:
          executor: NumpyIndexer
          filter_by: $FILTER_BY
      - !KVIndexDriver
        with:
          executor: BinaryPbIndexer
          filter_by: $FILTER_BY
    SearchRequest:
      - !VectorSearchDriver
        with:
          executor: NumpyIndexer
          filter_by: $FILTER_BY
      - !KVSearchDriver
        with:
          executor: BinaryPbIndexer
          filter_by: $FILTER_BY

                                 ''',
            '''
jtype: CompoundIndexer
metas:
  workspace: $TMP_WORKSPACE
components:
  - jtype: NumpyIndexer
    with:
      metric: euclidean
      index_filename: vec.gz
    metas:
      name: vecidx  # a customized name
  - jtype: BinaryPbIndexer
    with:
      index_filename: chunk.gz
    metas:
      name: kvidx  # a customized name
requests:
  on:
    IndexRequest:
      - jtype: VectorIndexDriver
        with:
          executor: NumpyIndexer
          filter_by: $FILTER_BY
      - jtype: KVIndexDriver
        with:
          executor: BinaryPbIndexer
          filter_by: $FILTER_BY
    SearchRequest:
      - jtype: VectorSearchDriver
        with:
          executor: NumpyIndexer
          filter_by: $FILTER_BY
      - jtype: KVSearchDriver
        with:
          executor: BinaryPbIndexer
          filter_by: $FILTER_BY

                                 ''',
        ),
    ],
)
def test_escape(original, escaped):
    assert JAML.escape(original, include_unknown_tags=False).strip() == escaped.strip()
    assert (
        JAML.unescape(
            JAML.escape(original, include_unknown_tags=False),
            include_unknown_tags=False,
        ).strip()
        == original.strip()
    )


def test_enum_dump():
    assert JAML.dump(SocketType.PUSH_CONNECT).strip() == '"PUSH_CONNECT"'
