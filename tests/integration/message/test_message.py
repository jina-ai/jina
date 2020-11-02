import pytest

from jina.clients.python.request import _generate
from jina.logging.profile import TimeContext
from jina.proto import jina_pb2
from tests import random_docs

num_reqs, num_docs = 10, 1000


@pytest.mark.skip('this is for jina < 0.7.3 to showcase the performance issue')
def test_all_in_one_request():
    recv = [add_envelope(r, 'test', '123') for r in _generate(random_docs(num_docs))]
    with TimeContext('serialize and deserialize'):
        for _ in range(num_reqs):  # mimic multipic pods
            sent = [msg.SerializeToString() for msg in recv]  # mimic sent

            # mimic receive
            recv.clear()
            for m in sent:
                msg = jina_pb2.Message()
                msg.ParseFromString(m)
                msg.envelope.request_id += 'r'
                recv.append(msg)

    for r in recv:
        assert r.envelope.request_id.endswith('r' * num_reqs)


@pytest.mark.skip('this is for jina < 0.7.3 to showcase the performance issue')
def test_envelope_in_sep_request():
    """ ser/des on envelope only much faster

    :return:
    """
    recv = [(rr.envelope, rr.request.SerializeToString()) for rr in
            (add_envelope(r, 'test', '123') for r in _generate(random_docs(num_docs)))]
    with TimeContext('serialize and deserialize'):
        for _ in range(num_reqs):  # mimic chaining _pass, no need to deserialize request
            sent = [(msg[0].SerializeToString(), msg[1]) for msg in recv]  # mimic sent

            # mimic receive
            recv.clear()
            for m in sent:
                msg = jina_pb2.Envelope()
                msg.ParseFromString(m[0])
                msg.request_id += 'r'
                recv.append((msg, m[1]))

    for r in recv:
        assert r[0].request_id.endswith('r' * num_reqs)
