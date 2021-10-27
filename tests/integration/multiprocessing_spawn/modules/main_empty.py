from multiprocessing import get_start_method

import jina


def run():
    from exec import Exec

    with jina.Flow().add() as f:
        pass


if __name__ == '__main__':
    assert get_start_method() == 'spawn'
    run()
