from jina.executors.encoders.nlp.transformer import TransformerTFEncoder, TransformerTorchEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class PytorchTestCase(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class PytorchTestCasePollingMean(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            polling_strategy='mean',
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class PytorchTestCasePollingMin(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            polling_strategy='min',
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class PytorchTestCasePollingMax(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            polling_strategy='max',
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class TfTestCase(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class TfTestCasePollingMean(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            polling_strategy='mean',
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class TfTestCasePollingMin(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            polling_strategy='min',
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class TfTestCasePollingMax(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            polling_strategy='max',
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class XLNetPytorchTestCase(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetPytorchTestCasePollingMean(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            polling_strategy='mean',
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetPytorchTestCasePollingMax(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            polling_strategy='max',
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetPytorchTestCasePollingMin(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            polling_strategy='min',
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetTFTestCase(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetTFTestCaseCasePollingMean(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            polling_strategy='mean',
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetTFTestCaseCasePollingMax(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            polling_strategy='max',
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetTFTestCaseCasePollingMin(NlpTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_output_dim = 768

    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            polling_strategy='min',
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)
