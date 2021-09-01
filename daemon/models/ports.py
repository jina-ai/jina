from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class Ports(BaseModel):
    """Port names"""

    port_in: Optional[int]
    port_out: Optional[int]
    port_ctrl: Optional[int]
    port_expose: Optional[int]

    def __len__(self):
        return len(self.__fields_set__)


class PortMapping(BaseModel):
    """Used to set the additional port mappings in partial-daemon"""

    pod_name: str
    pea_name: str
    ports: Ports


class PortMappings(BaseModel):
    """Pydantic model for list of PortMappings"""

    __root__: List[PortMapping]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item: Union[str, int]):
        if isinstance(item, int):
            return self.__root__[item]
        elif isinstance(item, str):
            for mapping in self.__root__:
                if mapping.pea_name == item:
                    return mapping
                elif mapping.pod_name == item:
                    return mapping

    @property
    def ports(self) -> List[int]:
        """Get all ports in current model

        :return: list of ports
        """
        return [
            port
            for mapping in self.__root__
            for port in mapping.ports.__dict__.values()
            if port is not None
        ]

    @property
    def docker_ports(self) -> Dict[str, int]:
        """Get all ports for docker client

        :return: dict of ports for docker-py syntax
        """
        return {f'{port}/tcp': port for port in self.ports}

    @property
    def pod_names(self) -> List[str]:
        """Get all pod names

        :return: unique list of pod names
        """
        return list(set(mapping.pod_name for mapping in self.__root__))

    @property
    def pea_names(self) -> List[str]:
        """Get all pea names

        :return: list of pea names
        """
        return [mapping.pea_name for mapping in self.__root__]
