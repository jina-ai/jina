import sys
import time

from .test_pb2 import unitProto, skipProto, populatedProto


def test_serialization():
    pop = populatedProto()
    for i in range(1000):
        unit = pop.units.add()
        unit.a = 'test'

    print(f' getsizeof {sys.getsizeof(pop.units)}')

    skip = skipProto()
    skip.units = pop.SerializeToString()
    print(f' getsizeof {sys.getsizeof(skip.units)}')

    start = time.time()
    pop_serialized = pop.SerializeToString()
    end = time.time() - start
    print(f'Populated serialization took {end * 1000} ms')
    start = time.time()
    skip_serialized = skip.SerializeToString()

    end = time.time() - start
    print(f'Skip serialization took {end * 1000} ms')

    start = time.time()
    deserialize_populated = populatedProto.FromString(pop_serialized)
    end = time.time() - start
    print(f'Populated deserialization took {end * 1000} ms')

    start = time.time()
    deserialize_skip = skipProto.FromString(skip_serialized)
    end = time.time() - start
    print(f'Skip deserialization took {end * 1000} ms')
    new_pop = populatedProto.FromString(deserialize_skip.units)
    for unit in new_pop.units:
        assert unit.a == 'test'
