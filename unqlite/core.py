from contextlib import contextmanager
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
    return True

def kv_callback(fn):
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
        return handle_return_value(unqlite_close(self._unqlite))

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
        return handle_return_value(unqlite_kv_store(
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
            -1,
            value,
            len(value)))

    def exists(self, key):
        length = unqlite_int64(0)
        key = str(key)
        return unqlite_kv_fetch(
            self._unqlite,
            key,
            -1,
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
        elif rc == UNQLITE_NOTFOUND:
            raise KeyError(key)
        else:
            handle_return_value(rc)

    def fetch_cb(self, key, callback):
        if not hasattr(callback, '_c_callback'):
            callback = kv_callback(callback)
        rc = unqlite_kv_fetch_callback(
            self._unqlite,
            key,
            -1,
            callback._c_callback,
            None)
        if rc == UNQLITE_NOTFOUND:
            raise KeyError(key)
        return handle_return_value(rc)

    def delete(self, key):
        key = str(key)
        return handle_return_value(unqlite_kv_delete(
            self._unqlite,
            key,
            -1))

    __getitem__ = fetch
    __setitem__ = store
    __delitem__ = delete
    __contains__ = exists

    def VM(self):
        return VM(self._unqlite)

    @contextmanager
    def compile_script(self, code):
        vm = self.VM()
        vm.compile(code)
        with vm:
            yield vm

    @contextmanager
    def compile_file(self, filename):
        vm = self.VM()
        vm.compile_file(filename)
        with vm:
            yield vm

    # Transaction helpers. Currently these do not seem to work, not sure why.
    def begin(self):
        return handle_return_value(unqlite_begin(self._unqlite))

    def commit(self):
        return handle_return_value(unqlite_commit(self._unqlite))

    def rollback(self):
        return handle_return_value(unqlite_rollback(self._unqlite))

    def transaction(self):
        return transaction(self)

    def commit_on_success(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with self.transaction():
                return fn(*args, **kwargs)
        return wrapper

    # Cursor helpers.
    def cursor(self):
        return Cursor(self._unqlite)


class Cursor(object):
    def __init__(self, unqlite):
        self._unqlite = unqlite
        self._cursor = POINTER(unqlite_kv_cursor)()
        handle_return_value(unqlite_kv_cursor_init(
            self._unqlite,
            byref(self._cursor)))

    def close(self):
        handle_return_value(unqlite_kv_cursor_release(
            self._unqlite,
            self._cursor))
        self._cursor = None

    def seek(self, key, flags=UNQLITE_CURSOR_MATCH_EXACT):
        handle_return_value(unqlite_kv_cursor_seek(
            self._cursor,
            key,
            -1,
            flags))

    def first(self):
        return unqlite_kv_cursor_first_entry(self._cursor)

    def last(self):
        return unqlite_kv_cursor_last_entry(self._cursor)

    def is_valid(self):
        return bool(unqlite_kv_cursor_valid_entry(self._cursor))

    def next(self):
        return handle_return_value(unqlite_kv_cursor_next_entry(self._cursor))

    def previous(self):
        return handle_return_value(unqlite_kv_cursor_prev_entry(self._cursor))

    def reset(self):
        return handle_return_value(unqlite_kv_cursor_reset(self._cursor))

    def delete(self):
        return handle_return_value(unqlite_kv_cursor_delete_entry(
            self._cursor))

    def key(self, bufsize=4096):
        buf = create_string_buffer(bufsize)
        buflen = unqlite_int64(bufsize)
        handle_return_value(unqlite_kv_cursor_key(
            self._cursor,
            byref(buf),
            byref(buflen)))
        return buf.raw[:buflen.value]

    def value(self, bufsize=4096):
        buf = create_string_buffer(bufsize)
        buflen = unqlite_int64(bufsize)
        handle_return_value(unqlite_kv_cursor_data(
            self._cursor,
            byref(buf),
            byref(buflen)))
        return buf.raw[:buflen.value]

    def _make_callback(self, unqlite_fn, user_fn):
        if not hasattr(user_fn, '_c_callback'):
            user_fn = kv_callback(user_fn)
        handle_return_value(unqlite_fn(
            self._cursor,
            user_fn._c_callback,
            None))
        return user_fn

    def key_callback(self, fn):
        return self._make_callback(unqlite_kv_cursor_key_callback, fn)

    def value_callback(self, fn):
        return self._make_callback(unqlite_kv_cursor_data_callback, fn)

    def __iter__(self):
        return CursorIterator(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._cursor is not None:
            self.close()


class CursorIterator(object):
    def __init__(self, cursor):
        self._cursor = cursor

    def next(self):
        if self._cursor.is_valid():
            res = (self._cursor.key(), self._cursor.value())
            self._cursor.next()
            return res
        else:
            raise StopIteration


class VM(object):
    def __init__(self, unqlite):
        self._unqlite = unqlite
        self._vm = None

    def compile(self, code):
        self._vm = POINTER(unqlite_vm)()
        return handle_return_value(unqlite_compile(
            self._unqlite,
            code,
            -1,
            byref(self._vm)))

    def compile_file(self, filename):
        self._vm = POINTER(unqlite_vm)()
        return handle_return_value(unqlite_compile_file(
            self._unqlite,
            filename,
            byref(self._vm)))

    def close(self):
        res = handle_return_value(unqlite_vm_release(self._vm))
        self._vm = None
        return res

    def reset(self):
        return handle_return_value(unqlite_vm_reset(self._unqlite))

    def execute(self):
        return handle_return_value(unqlite_vm_exec(self._vm))

    def config(self, verb, *args):
        return handle_return_value(_unqlite_lib.unqlite_vm_config(
            self._vm,
            verb,
            *args))

    def create_var(self, key, value):
        """
        Register a foreign variable within the Jx9 script. The key should
        not contain a dollar sign.
        """
        # The value should be created using `create_scalar()` or
        # `create_array()`.
        pass

    def create_scalar(self, value):
        scalar = Value(self, unqlite_vm_new_scalar(self._vm))

    def create_array(self, value):
        arr = Value(self, unqlite_vm_new_array(self._vm))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._vm is not None:
            self.close()

class Value(object):
    def __init__(self, vm, value_ptr):
        self.vm = vm
        self.value_ptr = value_ptr



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
