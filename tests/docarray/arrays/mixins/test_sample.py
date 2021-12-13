import pytest

from docarray import DocumentArray, DocumentArrayMemmap


def da_and_dam(N):
    da = DocumentArray.empty(N)
    dam = DocumentArrayMemmap.empty(N)
    return da, dam


@pytest.mark.parametrize('da', da_and_dam(100))
def test_sample(da):
    sampled = da.sample(1)
    assert len(sampled) == 1
    sampled = da.sample(5)
    assert len(sampled) == 5
    assert isinstance(sampled, DocumentArray)
    with pytest.raises(ValueError):
        da.sample(101)  # can not sample with k greater than lenth of document array.


@pytest.mark.parametrize('da', da_and_dam(100))
def test_sample_with_seed(da):
    sampled_1 = da.sample(5, seed=1)
    sampled_2 = da.sample(5, seed=1)
    sampled_3 = da.sample(5, seed=2)
    assert len(sampled_1) == len(sampled_2) == len(sampled_3) == 5
    assert sampled_1 == sampled_2
    assert sampled_1 != sampled_3


@pytest.mark.parametrize('da', da_and_dam(100))
def test_shuffle(da):
    shuffled = da.shuffle()
    assert len(shuffled) == len(da)
    assert isinstance(shuffled, DocumentArray)
    ids_before_shuffle = [d.id for d in da]
    ids_after_shuffle = [d.id for d in shuffled]
    assert ids_before_shuffle != ids_after_shuffle
    assert sorted(ids_before_shuffle) == sorted(ids_after_shuffle)


@pytest.mark.parametrize('da', da_and_dam(100))
def test_shuffle_with_seed(da):
    shuffled_1 = da.shuffle(seed=1)
    shuffled_2 = da.shuffle(seed=1)
    shuffled_3 = da.shuffle(seed=2)
    assert len(shuffled_1) == len(shuffled_2) == len(shuffled_3) == len(da)
    assert shuffled_1 == shuffled_2
    assert shuffled_1 != shuffled_3
