### Document structures. An idea on how the input for the training Executors could work.
### Naming to be worked on

class TripletLossDocumentInput(Document):

    # For Metric Learning, one common interface, is to have batches of 3 documents. One is the anchor, which is supposed to be the reference,
    # one is the positive and the other is the negative.
    # the training procedure will try to push the embedding of the positive one close to the embedding of the anchor, and move the negative embedding far from the anchor one

    @property
    def positive(self):
        return self.chunks[0]

    @property
    def negative(self):
        return self.chunks[1]

    @property
    def anchor(self):
        return self.chunks[2]


class SiameseLossDocumentInput(Document):

    # For Metric Learning, one common interface, is to have batches of 2 documents, together with a tag determining if they are positive or negative pairs.
    # the training procedure will try to push the embeddings of the pairs together if they are positive, or far apart if they are negative

    @property
    def first(self):
        return self.chunks[0]

    @property
    def second(self):
        return self.chunks[1]

    @property
    def positive(self) -> boolean:
        return self.tags['positive']

class CrossEntropyLossDocumentInput(Document):

    # For Classification learning, and for some easy embedding learning procedures, using cross entropy loss can be good enough (then u can extract middle layers)
    # The training batch request would be formed by documents with some content and labels for classification
    @property
    def label(self):
        return self.tags['label']


class RankerTrainDocumentInput(Document)
    # For Learning To Rank models, a Document with matches attached can be used to extract `query` and `match` metas as in the RankerExecutor


### Drivers class structure

class BaseTrainDriver(BaseExecutableDriver):
    def __init__(
            self,
            executor: Optional[str] = None,
            method: str = 'train',
            *args,
            **kwargs,
    ):
        super().__init__(executor, method, *args, **kwargs)


class TripletLossTrainDriver(BaseTrainDriver):
    def __init__(
            self,
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        contrastive_training_docs = TripletLossDocSet(docs)
        positives_content, negatives_content, anchors_content = contrastive_training_docs.extract_positives_negatives_anchors()
        self.exec_fn(positives_content, negatives_content, anchors_content)


class SiameseLossTrainDriver(BaseTrainDriver):
    def __init__(
            self,
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        contrastive_training_docs = SiameseLossTrainDriver(docs)
        first, second, positive = contrastive_training_docs.extract_first_second_positive_labels()
        self.exec_fn(first, second, positive)


class CrossEntropyLossTrainDriver(BaseTrainDriver):
    def __init__(
            self,
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        contents = docs.get_contents()
        labels = docs.get_attrs('tags__label')
        self.exec_fn(contents, labels)


class RankerTrainDriver(BaseTrainDriver):
    def __init__(
            self,
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        query_meta = docs.get_metas()
        matches_metas = [[match.get_metas() for match in doc.matches] for doc in docs]
        self.exec_fn(query_meta, matches_metas)


### Executors class structure
class DumpMixin():

    def load_from_dump(self):
        pass

    def dump(self):
        pass


class BaseTrainExecutor(DumpMixin, BaseExecutor):

    def __init__(self,
                 dump_persistor: DumpPersistor):
        pass

    def save(self):
        # this to be done in subclasses where the `artifact` to store is known
        self.dump(self.model)

    def load_from_dump(self, *data):
        dump_persistor.load_from_dump(data)

    def dump(self, *data):
        dump_persistor.dump(data)

    def train(
            self, *args, **kwargs
    ) -> None:  # what should be returned?
        # Inside these functions, a `batch` is expected to be processed.
        raise NotImplementedError


class TripletLossTrainExecutor(BaseTrainExecutor):

    # can be used to train encoders with `contrastive loss` strategy. Also useful for Classifiers
    def train(
            self, positive: 'np.ndarray', negative: 'np.ndarray', anchor: Optional['np.ndarray'], *args, **kwargs
    ) -> None:
        raise NotImplementedError


class SiameseLossTrainExecutor(BaseTrainExecutor):

    # can be used to train encoders with `contrastive loss` strategy. Also useful for Classifiers
    def train(
            self, first: 'np.ndarray', second: 'np.ndarray', positive: 'np.ndarray[boolean]', *args, **kwargs
    ) -> None:
        raise NotImplementedError


class CrossEntropyLossTrainExecutor(BaseTrainExecutor):

    # can be used to train encoders with naive `cross entropy` strategy. Also useful for Classifiers
    def train(
            self, data: 'np.ndarray', label: 'np.ndarray', *args, **kwargs
    ) -> None:
        raise NotImplementedError


class RankerTrainExecutor(BaseTrainExecutor):

    # Interface for training rankers like LightGBM Ranker
    def train(
            self, queries_metas: List[Dict], matches_metas: List[List[Dict]], *args, **kwargs
    ) -> None:
        raise NotImplementedError