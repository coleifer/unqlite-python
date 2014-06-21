from unqlite._unqlite import *
from unqlite._unqlite import _libs as _c_libraries

def handle_return_value(rc):
    if rc != UNQLITE_OK:
        raise Exception({
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

    def store(self, key, value):
        key, value = str(key), str(value)
        handle_return_value(unqlite_kv_store(
            self._unqlite,
            key,
            len(key),
            value,
            len(value)))

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
            len(key),
            byref(buf),
            byref(nbytes))
        if rc == UNQLITE_OK:
            return buf.raw[:nbytes.value]
        elif rc == SXERR_NOTFOUND:
            raise KeyError(key)
        handle_return_value(rc)

    def delete(self, key):
        key = str(key)
        handle_return_value(unqlite_kv_delete(self._unqlite, key, len(key)))

    __getitem__ = fetch
    __setitem__ = store
    __delitem__ = delete
    __contains__ = exists
