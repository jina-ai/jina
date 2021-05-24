import uuid
from typing import Dict, Union

from jina.helper import random_identity
from .enums import IDLiterals


class DaemonID(str):
    """
    Custom datatype defining an ID in Daemon
    """

    pattern = f'^({"|".join(IDLiterals.values)})-[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$'

    def __new__(cls, value: Union[str, IDLiterals], *args, **kwargs) -> 'DaemonID':
        return str.__new__(cls, cls.validate(value), *args, **kwargs)

    @property
    def jtype(self):
        return self.split('-', 1)[0]

    @property
    def jid(self):
        return self.split('-', 1)[1]

    @property
    def type(self):
        return self.jtype[1:]

    @property
    def tag(self):
        return f'{self.jtype}:{self.jid}'

    @classmethod
    def __get_validators__(cls):
        yield cls.pydantic_validate

    @classmethod
    def validate(cls, value: str):
        if not isinstance(value, str):
            raise TypeError('Malformed DaemonID: must be a string')

        jtype, *jid = value.split('-', 1)
        if jtype not in IDLiterals.values:
            raise TypeError(
                f'Malformed DaemonID: \'{jtype}\' not in {IDLiterals.values}'
            )

        if not jid:
            jid = random_identity()
        else:
            try:
                jid = uuid.UUID(*jid)
            except ValueError:
                raise TypeError(f'Malformed DaemonID: {*jid,} is not a valid UUID')

        return f'{jtype}-{jid}'

    @classmethod
    def pydantic_validate(cls, value: str):
        return cls(cls.validate(value))

    @classmethod
    def __modify_schema__(cls, field_schema: Dict):
        field_schema.update(pattern=cls.pattern)

    def __repr__(self):
        return f'DaemonID({super().__repr__()})'
