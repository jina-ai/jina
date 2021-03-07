from .custom import build_pydantic_model

FlowModel = build_pydantic_model(model_name='FlowModel', module='flow')
PodModel = build_pydantic_model(model_name='PodModel', module='pod')
PeaModel = build_pydantic_model(model_name='PeaModel', module='pea')
