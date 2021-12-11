from typing import (
    Type,
    TYPE_CHECKING,
    Optional,
    overload,
    Union,
    List,
    TextIO,
    Dict,
    Iterable,
)

if TYPE_CHECKING:
    from ....helper import T
    import numpy as np
    import csv


class FromGeneratorMixin:
    """Provide helper functions filling a :class:`DocumentArray`-like object with a generator."""

    @classmethod
    def _from_generator(cls: Type['T'], meth: str, *args, **kwargs) -> 'T':
        from ....document import generators

        from_fn = getattr(generators, meth)
        da_like = cls()
        da_like.extend(from_fn(*args, **kwargs))
        return da_like

    @classmethod
    @overload
    def from_ndarray(
        cls: Type['T'],
        array: 'np.ndarray',
        axis: int = 0,
        size: Optional[int] = None,
        shuffle: bool = False,
    ) -> 'T':
        """Build from a numpy array.

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the numpy data source beforehand
        """
        ...

    @classmethod
    def from_ndarray(cls: Type['T'], *args, **kwargs) -> 'T':
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return cls._from_generator('from_ndarray', *args, **kwargs)

    @classmethod
    @overload
    def from_files(
        cls: Type['T'],
        patterns: Union[str, List[str]],
        recursive: bool = True,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
        read_mode: Optional[str] = None,
        to_dataturi: bool = False,
    ) -> 'T':
        """Build from a list of file path or the content of the files.

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files
            and zero or more directories and subdirectories
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file is opened.
            'r' for reading in text mode, 'rb' for reading in binary mode.
            If `read_mode` is None, will iterate over filenames.
        :param to_dataturi: if set, then the Document.uri will be filled with DataURI instead of the plan URI
        """
        ...

    @classmethod
    def from_files(cls: Type['T'], *args, **kwargs) -> 'T':
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return cls._from_generator('from_files', *args, **kwargs)

    @classmethod
    @overload
    def from_csv(
        cls: Type['T'],
        file: Union[str, TextIO],
        field_resolver: Optional[Dict[str, str]] = None,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
        dialect: Union[str, 'csv.Dialect'] = 'excel',
    ) -> 'T':
        """Build from CSV.

        :param file: file paths or file handler
        :param field_resolver: a map from field names defined in JSON, dict to the field
                names defined in Document.
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param dialect: define a set of parameters specific to a particular CSV dialect. could be a string that represents
            predefined dialects in your system, or could be a :class:`csv.Dialect` class that groups specific formatting
            parameters together. If you don't know the dialect and the default one does not work for you,
            you can try set it to ``auto``.
        """
        ...

    @classmethod
    def from_csv(cls: Type['T'], *args, **kwargs) -> 'T':
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return cls._from_generator('from_csv', *args, **kwargs)

    @classmethod
    @overload
    def from_huggingface_datasets(
        cls: Type['T'],
        dataset_path: str,
        field_resolver: Optional[Dict[str, str]] = None,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
        filter_fields: bool = False,
        **datasets_kwargs,
    ) -> 'T':
        """Build from Hugging Face Datasets. Yields documents.

        This function helps to load datasets from Hugging Face Datasets Hub
        (https://huggingface.co/datasets) in Jina. Additional parameters can be
        passed to the ``datasets`` library using keyword arguments. The ``load_dataset``
        method from ``datasets`` library is used to load the datasets.

        :param dataset_path: a valid dataset path for Hugging Face Datasets library.
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
                names defined in Protobuf. This is only used when the given ``document`` is
                a JSON string or a Python dict.
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param filter_fields: specifies whether to filter the dataset with the fields
                given in ```field_resolver`` argument.
        :param **datasets_kwargs: additional arguments for ``load_dataset`` method
                from Datasets library. More details at
                https://huggingface.co/docs/datasets/package_reference/loading_methods.html#datasets.load_dataset
        """
        ...

    @classmethod
    def from_huggingface_datasets(cls: Type['T'], *args, **kwargs) -> 'T':
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return cls._from_generator('from_huggingface_datasets', *args, **kwargs)

    @classmethod
    @overload
    def from_ndjson(
        cls: Type['T'],
        fp: Iterable[str],
        field_resolver: Optional[Dict[str, str]] = None,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
    ) -> 'T':
        """Build from line separated JSON. Yields documents.

        :param fp: file paths
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
                names defined in Protobuf. This is only used when the given ``document`` is
                a JSON string or a Python dict.
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        """
        ...

    @classmethod
    def from_ndjson(cls: Type['T'], *args, **kwargs) -> 'T':
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return cls._from_generator('from_ndjson', *args, **kwargs)

    @classmethod
    @overload
    def from_lines(
        cls: 'T',
        lines: Optional[Iterable[str]] = None,
        filepath: Optional[str] = None,
        read_mode: str = 'r',
        line_format: str = 'json',
        field_resolver: Optional[Dict[str, str]] = None,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
    ) -> 'T':
        """Build from lines, json and csv. Yields documents or strings.

        :param lines: a list of strings, each is considered as a document
        :param filepath: a text file that each line contains a document
        :param read_mode: specifies the mode in which the file
                    is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param line_format: the format of each line ``json`` or ``csv``
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
                names defined in Protobuf. This is only used when the given ``document`` is
                a JSON string or a Python dict.
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        """
        ...

    @classmethod
    def from_lines(cls: Type['T'], *args, **kwargs) -> 'T':
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return cls._from_generator('from_lines', *args, **kwargs)
