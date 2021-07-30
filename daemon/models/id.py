import uuid
from typing import Dict, Union

from jina.helper import random_identity
from .enums import IDLiterals


class DaemonID(str):
    """Custom datatype defining an ID in Daemon"""

    pattern = f'^({"|".join(IDLiterals.values)})-[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$'

    def __new__(cls, value: Union[str, IDLiterals], *args, **kwargs) -> 'DaemonID':
        """Validate str and create `DaemonID` object

        :param value: input value
        :param args: args
        :param kwargs: keyword args
        :return: `DaemonID` object
        """
        return str.__new__(cls, cls.validate(value), *args, **kwargs)

    @property
    def jtype(self) -> str:
        """Get IDLiterals from DaemonID

        :return: get jtype
        """

        return self.split('-', 1)[0]

    @property
    def jid(self):
        """Get uuid from DaemonID

        :return: get uuid
        """
        return self.split('-', 1)[1]

    @property
    def type(self):
        """Get jina object type from DaemonID

        :return: get type
        """
        return self.jtype[1:]

    @property
    def tag(self):
        """Get tag (: separated type & id) from DaemonID

        :return: get tag
        """
        return f'{self.jtype}:{self.jid}'

    @classmethod
    def __get_validators__(cls):
        yield cls.pydantic_validate

    @classmethod
    def validate(cls, value: str) -> str:
        """Validate DaemonID

        :param value: str to be validated
        :return: str of type DaemonID
        """
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
        """Validate method for pydantic

        :param value: str to be validated
        :return: str of type DaemonID
        """
        return cls(cls.validate(value))

    @classmethod
    def __modify_schema__(cls, field_schema: Dict):
        field_schema.update(pattern=cls.pattern)

    def __repr__(self):
        return f'DaemonID({super().__repr__()})'


def daemonize(identity: str, kind: str = 'workspace') -> DaemonID:
    """Convert to DaemonID

    :param identity: uuid or DaemonID
    :param kind: defaults to 'workspace'
    :return: DaemonID from identity
    """
    try:
        return DaemonID(identity)
    except TypeError:
        return DaemonID(f'j{kind}-{identity}')
