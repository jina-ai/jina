from pathlib import Path


def physical_size(directory: str) -> int:
    """Return the size of the given directory in bytes

    :param directory: directory as :str:
    :return: byte size of the given directory
    """
    root_directory = Path(directory)
    return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
