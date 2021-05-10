from jina.executors.indexers.filtering.inverted_be_index import (
    BooleanExpression,
    BooleanExpressionInvertedIndex,
)


def test_boolean_expression():
    lookups = {'tags__id': 2, 'text__contains': 'hello'}

    boolean_expression = BooleanExpression(lookups=lookups)
    assert str(boolean_expression) == 'tags__id:2-text__contains:hello'
    assert hash(boolean_expression) is not None
    assert hash(boolean_expression) == hash(BooleanExpression(lookups=lookups))

    assert boolean_expression.k == 2

    assert len(boolean_expression.predicates) == 2

    for predicate in boolean_expression:
        assert isinstance(predicate, BooleanExpression)
        assert predicate.k == 1


def test_be_inverted_index_simple():
    lookups_1 = {'tags__size': 'm', 'tags__category': 'dress'}
    lookups_2 = {'tags__size': 'm', 'tags__category': 'trousers'}
    lookups_3 = {'tags__size': 'l', 'tags__category': 'dress'}
    lookups_4 = {'tags__size': 'l', 'tags__category': 'trousers'}
    lookups_5 = {'tags__size': 's'}

    indexer = BooleanExpressionInvertedIndex()
    indexer.add(lookups_1)
    indexer.add(lookups_2)
    indexer.add(lookups_3)
    indexer.add(lookups_4)
    indexer.add(lookups_5)

    assert len(indexer.ids) == 5
    assert len(indexer.inverted_indexes.keys()) == 2  # 2 ks
    assert len(indexer.inverted_indexes[1]) == 1
    assert len(indexer.inverted_indexes[2]) == 4
    assert sorted(indexer.inverted_indexes.keys()) == [1, 2]
    assert len(indexer.inverted_indexes[1].keys()) == 1
    assert len(indexer.inverted_indexes[2].keys()) == 4
    for key in indexer.inverted_indexes[2].keys():
        assert len(indexer.inverted_indexes[2][key]) == 2
    assert indexer.max_k == 2

    assert len(indexer.query(lookups=lookups_1)) == 1
    assert len(indexer.query(lookups=lookups_2)) == 1
    assert len(indexer.query(lookups=lookups_3)) == 1
    assert len(indexer.query(lookups=lookups_4)) == 1
    assert len(indexer.query(lookups=lookups_5)) == 1

    assert indexer.query(lookups=lookups_1)[0] == BooleanExpression(lookups=lookups_1)
    assert indexer.query(lookups=lookups_2)[0] == BooleanExpression(lookups=lookups_2)
    assert indexer.query(lookups=lookups_3)[0] == BooleanExpression(lookups=lookups_3)
    assert indexer.query(lookups=lookups_4)[0] == BooleanExpression(lookups=lookups_4)
    assert indexer.query(lookups=lookups_5)[0] == BooleanExpression(lookups=lookups_5)

    assert sorted(indexer.query(lookups={'tags__size': 'm'})) == sorted(
        [
            BooleanExpression(lookups=lookups_1),
            BooleanExpression(lookups=lookups_2),
        ]
    )
    assert sorted(indexer.query(lookups={'tags__size': 'l'})) == sorted(
        [
            BooleanExpression(lookups=lookups_3),
            BooleanExpression(lookups=lookups_4),
        ]
    )
    assert sorted(indexer.query(lookups={'tags__category': 'dress'})) == sorted(
        [
            BooleanExpression(lookups=lookups_1),
            BooleanExpression(lookups=lookups_3),
        ]
    )
    assert sorted(indexer.query(lookups={'tags__category': 'trousers'})) == sorted(
        [
            BooleanExpression(lookups=lookups_2),
            BooleanExpression(lookups=lookups_4),
        ]
    )
    assert sorted(indexer.query(lookups={'tags__size': 's'})) == sorted(
        [BooleanExpression(lookups=lookups_5)]
    )

    assert indexer.query(lookups={'tags__size': 'r'}) == []
