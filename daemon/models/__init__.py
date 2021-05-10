from enum import Enum

from .custom import build_pydantic_model

FlowModel = build_pydantic_model(model_name='FlowModel', module='flow')
PodModel = build_pydantic_model(model_name='PodModel', module='pod')
PeaModel = build_pydantic_model(model_name='PeaModel', module='pea')


class UpdateOperationEnum(Enum):
    """Represents the type of operation to perform in the update

    We consider these an `update` operation since they **change** the underlying state
    """

    rolling_update = 'rolling_update'
    dump = 'dump'
