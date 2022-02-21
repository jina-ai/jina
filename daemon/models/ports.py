from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class Ports(BaseModel):
    """Port names"""

    port: Optional[int]

    def __len__(self):
        return len(self.__fields_set__)


class PortMapping(BaseModel):
    """Used to set the additional port mappings in partial-daemon"""

    deployment_name: str
    pod_name: str
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
                if mapping.pod_name == item:
                    return mapping
                elif mapping.deployment_name == item:
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
    def deployment_names(self) -> List[str]:
        """Get all deployment names

        :return: unique list of deployment names
        """
        return list(set(mapping.deployment_name for mapping in self.__root__))

    @property
    def pod_names(self) -> List[str]:
        """Get all pod names

        :return: list of pod names
        """
        return [mapping.pod_name for mapping in self.__root__]
