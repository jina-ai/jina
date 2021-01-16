from fastapi.exceptions import HTTPException

from ...stores.base import BaseStore


def del_from_store(store: 'BaseStore', key):
    with store.session():
        try:
            del store[key]
        except KeyError:
            raise HTTPException(status_code=404, detail=f'{key} not found in {store!r}')


def clear_store(store: 'BaseStore'):
    with store.session():
        store.clear()


def add_store(store: 'BaseStore', *args, **kwargs):
    with store.session():
        try:
            _id = store.add(*args, **kwargs)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'{e!r}')
        return {
            'id': _id,
            'status': 'started'
        }
