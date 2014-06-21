from functools import wraps

from unqlite._unqlite import *
from unqlite._unqlite import _libs as _c_libraries
from unqlite._unqlite import _variadic_function

def handle_return_value(rc):
    if rc != UNQLITE_OK:
        raise Exception({
            UNQLITE_NOTFOUND: 'Key not found',
            UNQLITE_NOMEM: 'Out of memory',
            UNQLITE_ABORT: 'Executed command request an operation abort',
            UNQLITE_IOERR: 'OS error',
            UNQLITE_CORRUPT: 'Corrupt database',
            UNQLITE_LOCKED: 'Locked database',
            UNQLITE_BUSY: 'Database is locked by another thread/process',
            UNQLITE_DONE: 'Error: UNQLITE_DONE',
            UNQLITE_NOTIMPLEMENTED: 'Not implemented',
            UNQLITE_READ_ONLY: 'Database is in read-only mode',
        }.get(rc, 'Unknown exception: %s' % rc))

_unqlite_lib = _c_libraries['unqlite']

class UnQLite(object):
    """
    UnQLite database python bindings.
    """
    def __init__(self, database=':mem:', open_manually=False):
        self.database = database
        self._unqlite = POINTER(unqlite)()
        self._command_registry = {}
        if not open_manually:
            self.open()

    def open(self, flags=UNQLITE_OPEN_CREATE):
        rc = unqlite_open(byref(self._unqlite), self.database, flags)
        if rc != UNQLITE_OK:
            raise Exception('Unable to open UnQLite database')

    def close(self):
        handle_return_value(unqlite_close(self._unqlite))

    def config(self, verb, *args):
        return handle_return_value(_unqlite_lib.unqlite_config(
            self._unqlite,
            verb,
            *args))

    def _disable_autocommit(self):
        self.config(UNQLITE_CONFIG_DISABE_AUTO_COMMIT)

    def _set_max_page_cache(self, npages):
        self.config(UNQLITE_CONFIG_MAX_PAGE_CACHE, npages)

    # Key/Value interface.
    def store(self, key, value):
        key, value = str(key), str(value)
        handle_return_value(unqlite_kv_store(
            self._unqlite,
            key,
            -1,
            value,
            len(value)))

    def store_fmt(self, key, value, *params):
        return handle_return_value(_unqlite_lib.unqlite_kv_store_fmt(
            self._unqlite,
            str(key),
            -1,
            value,
            *params))

    def append(self, key, value):
        key, value = str(key), str(value)
        handle_return_value(unqlite_kv_append(
            self._unqlite,
            key,
            len(key),
            value,
            len(value)))

    def exists(self, key):
        length = unqlite_int64(0)
        key = str(key)
        return unqlite_kv_fetch(
            self._unqlite,
            key,
            len(key),
            None,
            byref(length)) == UNQLITE_OK

    def fetch(self, key, buf_size=4096, determine_buffer_size=False):
        key = str(key)
        buf = create_string_buffer(buf_size)
        nbytes = unqlite_int64(buf_size)
        rc = unqlite_kv_fetch(
            self._unqlite,
            key,
            -1,
            byref(buf),
            byref(nbytes))
        if rc == UNQLITE_OK:
            return buf.raw[:nbytes.value]
        elif rc == SXERR_NOTFOUND:
            raise KeyError(key)
        handle_return_value(rc)

    def fetch_cb(self, key, callback):
        if not hasattr(callback, '_c_callback'):
            callback = self.kv_callback(callback)
        rc = unqlite_kv_fetch_callback(
            self._unqlite,
            key,
            -1,
            callback._c_callback,
            None)
        if rc == UNQLITE_NOTFOUND:
            raise KeyError(key)
        return handle_return_value(rc)

    def kv_callback(self, fn):
        def cb_wrapper(data_ptr, data_len, user_data_ptr):
            data = (c_char * data_len).from_address(data_ptr).raw
            try:
                fn(data)
            except:
                return UNQLITE_ABORT
            return UNQLITE_OK

        c_callback = CFUNCTYPE(
            UNCHECKED(c_int),
            POINTER(None),
            UNCHECKED(c_uint),
            POINTER(None))(cb_wrapper)

        fn._c_callback = c_callback
        fn._cb_wrapper = cb_wrapper

        return fn

    def delete(self, key):
        key = str(key)
        handle_return_value(unqlite_kv_delete(self._unqlite, key, len(key)))

    __getitem__ = fetch
    __setitem__ = store
    __delitem__ = delete
    __contains__ = exists

    # Transaction helpers. Currently these do not seem to work, not sure why.
    def begin(self):
        handle_return_value(unqlite_begin(self._unqlite))

    def commit(self):
        handle_return_value(unqlite_commit(self._unqlite))

    def rollback(self):
        handle_return_value(unqlite_rollback(self._unqlite))

    def transaction(self):
        return transaction(self)

    def commit_on_success(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with self.transaction():
                return fn(*args, **kwargs)
        return wrapper

    # Cursor helpers.


class transaction(object):
    def __init__(self, unqlite):
        self.unqlite = unqlite

    def __enter__(self):
        self.unqlite.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.unqlite.rollback()
        else:
            try:
                self.unqlite.commit()
            except:
                self.unqlite.rollback()
                raise
