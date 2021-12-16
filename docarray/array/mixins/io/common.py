from typing import Union, TextIO, BinaryIO, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from ....helper import T


class CommonIOMixin:
    """The common IO helper function for arrays. """

    def save(
        self, file: Union[str, TextIO, BinaryIO], file_format: str = 'json'
    ) -> None:
        """Save array elements into a JSON, a binary file or a CSV file.

        :param file: File or filename to which the data is saved.
        :param file_format: `json` or `binary` or `csv`. JSON and CSV files are human-readable,
            but binary format gives much smaller size and faster save/load speed. Note that, CSV file has very limited
            compatability, complex DocumentArray with nested structure can not be restored from a CSV file.
        """
        if file_format == 'json':
            self.save_json(file)
        elif file_format == 'binary':
            self.save_binary(file)
        elif file_format == 'csv':
            self.save_csv(file)
        else:
            raise ValueError('`format` must be one of [`json`, `binary`, `csv`]')

    @classmethod
    def load(
        cls: Type['T'], file: Union[str, TextIO, BinaryIO], file_format: str = 'json'
    ) -> 'T':
        """Load array elements from a JSON or a binary file, or a CSV file.

        :param file: File or filename to which the data is saved.
        :param file_format: `json` or `binary` or `csv`. JSON and CSV files are human-readable,
            but binary format gives much smaller size and faster save/load speed. CSV file has very limited compatability,
            complex DocumentArray with nested structure can not be restored from a CSV file.

        :return: the loaded DocumentArray object
        """
        if file_format == 'json':
            return cls.load_json(file)
        elif file_format == 'binary':
            return cls.load_binary(file)
        elif file_format == 'csv':
            return cls.load_csv(file)
        else:
            raise ValueError('`format` must be one of [`json`, `binary`, `csv`]')
