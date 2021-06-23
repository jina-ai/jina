import uuid
import pytest
from pydantic import BaseModel
from daemon.models import DaemonID


VALID_JTYPES = ['jflow', 'jpod', 'jpea', 'jworkspace', 'jnetwork']


def test_jtype_only():
    for jtype in VALID_JTYPES:
        d = DaemonID(jtype)
        assert d.jtype == jtype
        assert uuid.UUID(d.jid)


def test_jtype_jid():
    an_id = uuid.uuid4()
    for jtype in VALID_JTYPES:
        d = DaemonID(f'{jtype}-{an_id}')
        assert d.jtype == jtype
        assert d.jid == str(an_id)
        assert d.tag == f'{jtype}:{an_id}'


def test_id_raise():
    an_id = uuid.uuid4()
    with pytest.raises(TypeError):
        DaemonID(an_id)

    with pytest.raises(TypeError):
        DaemonID('invalid')

    with pytest.raises(TypeError):
        DaemonID(f'invalid-{an_id}')

    with pytest.raises(TypeError):
        DaemonID(f'jflow-invalid')


def test_validate_id_in_pydantic_model():
    an_id = uuid.uuid4()

    class Model(BaseModel):
        id: DaemonID

    for jtype in VALID_JTYPES:
        Model(id=jtype)
        Model(id=f'{jtype}-{an_id}')

    with pytest.raises(ValueError):
        Model(id=f'invalid-{an_id}')

    with pytest.raises(ValueError):
        Model(id=an_id)

    with pytest.raises(ValueError):
        Model(id='a-string')
