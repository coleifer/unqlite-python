from contextlib import contextmanager
from functools import wraps

from unqlite._unqlite import *
from unqlite._unqlite import _libs as _c_libraries
from unqlite._unqlite import _variadic_function

DEFAULT_BUFFER_SIZE = 16384


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

def _value_to_string(ptr):
    nbytes = c_int()
    res = unqlite_value_to_string(ptr, pointer(nbytes))
    return res.raw[:nbytes.value]

def _array_fetch_cb(array_ptr, callback):
    c_callback = CFUNCTYPE(
        UNCHECKED(c_int),
        POINTER(unqlite_value),
        POINTER(unqlite_value),
        POINTER(None))(callback)
    unqlite_array_walk(array_ptr, c_callback, None)

def _value_to_list(ptr):
    accum = []
    def cb(key_ptr, value_ptr, user_data_ptr):
        accum.append(_convert_value(value_ptr))
        return UNQLITE_OK
    _array_fetch_cb(ptr, cb)
    return accum

def _value_to_dict(ptr):
    accum = {}
    def cb(key_ptr, value_ptr, user_data_ptr):
        accum[_convert_value(key_ptr)] = _convert_value(value_ptr)
        return UNQLITE_OK
    _array_fetch_cb(ptr, cb)
    return accum

def _convert_value(ptr):
    if unqlite_value_is_json_object(ptr):
        return _value_to_dict(ptr)
    elif unqlite_value_is_json_array(ptr):
        return _value_to_list(ptr)
    elif unqlite_value_is_string(ptr):
        return _value_to_string(ptr)
    elif unqlite_value_is_int(ptr):
        return unqlite_value_to_int(ptr)
    elif unqlite_value_is_float(ptr):
        return unqlite_value_to_double(ptr)
    elif unqlite_value_is_bool(ptr):
        return bool(unqlite_value_to_bool(ptr))
    elif unqlite_value_is_null(ptr):
        return None
    raise TypeError('Unrecognized type: %s' % ptr)

def wrap_foreign_function(fn):
    def inner(context, nargs, values):
        converted_args = [_convert_value(values[i]) for i in range(nargs)]
        context_wrapper = _Context(context)
        try:
            ret = fn(context_wrapper, *converted_args)
        except:
            return UNQLITE_ABORT
        else:
            context_wrapper.push_result(ret)
            return UNQLITE_OK

    c_callback = CFUNCTYPE(
        UNCHECKED(c_int),
        POINTER(unqlite_context),
        c_int,
        POINTER(POINTER(unqlite_value)))(inner)

    return c_callback, inner

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

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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

    def store_file(self, key, filename):
        ptr = c_void_p()
        size = unqlite_int64(os.stat(filename).st_size)
        handle_return_value(unqlite_util_load_mmaped_file(
            filename,
            byref(ptr),
            byref(size)))
        try:
            return handle_return_value(unqlite_kv_store(
                self._unqlite,
                key,
                -1,
                ptr,
                size))
        finally:
            unqlite_util_release_mmaped_file(ptr, size)

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

    def fetch(self, key, buf_size=DEFAULT_BUFFER_SIZE):
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
        rc = unqlite_kv_delete(
            self._unqlite,
            key,
            -1)
        if rc == UNQLITE_NOTFOUND:
            raise KeyError(key)
        return handle_return_value(rc)

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

    def collection(self, name):
        return Collection(self, name)

    # Utilities.
    def random_string(self, nbytes):
        buf = create_string_buffer(nbytes)
        handle_return_value(unqlite_util_random_string(
            self._unqlite,
            addressof(buf),
            nbytes))
        return buf.raw[:nbytes]

    def random_number(self):
        return unqlite_util_random_num(self._unqlite)

    # Library info.
    @property
    def lib_version(self):
        return str(unqlite_lib_version())

    @property
    def lib_signature(self):
        return str(unqlite_lib_signature())

    @property
    def lib_ident(self):
        return str(unqlite_lib_ident())

    @property
    def lib_is_threadsafe(self):
        return bool(unqlite_lib_is_threadsafe())

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

    def __iter__(self):
        return DBCursorIterator(self.cursor())

    def range(self, start_key, end_key, include_end_key=True):
        with self.cursor() as cursor:
            cursor.seek(start_key)
            for item in cursor.fetch_until(end_key, include_end_key):
                yield item

    def flush(self):
        with self.cursor() as curs:
            curs.first()
            while curs.is_valid():
                curs.delete()

    def __len__(self):
        ct = 0
        with self.cursor() as curs:
            curs.first()
            while curs.is_valid():
                ct += 1
                try:
                    curs.next()
                except StopIteration:
                    break
        return ct


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
        ret = unqlite_kv_cursor_next_entry(self._cursor)
        if ret == UNQLITE_DONE:
            raise StopIteration
        return handle_return_value(ret)

    def previous(self):
        return handle_return_value(unqlite_kv_cursor_prev_entry(self._cursor))

    def reset(self):
        return handle_return_value(unqlite_kv_cursor_reset(self._cursor))

    def delete(self):
        return handle_return_value(unqlite_kv_cursor_delete_entry(
            self._cursor))

    def _kv_cursor_value(self, unqlite_fn, bufsize):
        buf = create_string_buffer(bufsize)
        buflen = unqlite_int64(bufsize)
        handle_return_value(unqlite_fn(
            self._cursor,
            byref(buf),
            byref(buflen)))
        return buf.raw[:buflen.value]

    def key(self, bufsize=DEFAULT_BUFFER_SIZE):
        return self._kv_cursor_value(unqlite_kv_cursor_key, bufsize)

    def value(self, bufsize=DEFAULT_BUFFER_SIZE):
        return self._kv_cursor_value(unqlite_kv_cursor_data, bufsize)

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

    def fetch_count(self, ct):
        return CursorIterator(self, ct)

    def fetch_until(self, stop_key, include_stop_key=True):
        # Yield rows until `key` is reached.
        for key, value in self:
            if key == stop_key:
                if include_stop_key:
                    yield (key, value)
                raise StopIteration
            else:
                yield (key, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._cursor is not None:
            self.close()


class CursorIterator(object):
    def __init__(self, cursor, ct=None):
        self._cursor = cursor
        self._ct = ct or -1

    def next(self):
        if self._cursor.is_valid() and self._ct != 0:
            res = (self._cursor.key(), self._cursor.value())
            try:
                self._cursor.next()
            except StopIteration:
                pass
            self._ct -= 1
            return res
        else:
            raise StopIteration

    def __iter__(self):
        return self


class DBCursorIterator(CursorIterator):
    def __init__(self, cursor, ct=None):
        super(DBCursorIterator, self).__init__(cursor, ct)
        self._cursor.first()

    def next(self):
        try:
            return super(DBCursorIterator, self).next()
        except StopIteration:
            self._cursor.close()
            raise


class _ValueBase(object):
    def _set_value(self, ptr, python_value):
        if isinstance(python_value, unicode):
            unqlite_value_string(ptr, python_value.encode('utf-8'), -1)
        elif isinstance(python_value, basestring):
            unqlite_value_string(ptr, python_value, -1)
        elif isinstance(python_value, (list, tuple)):
            for item in python_value:
                item_ptr = self.create_value(item)
                handle_return_value(unqlite_array_add_elem(
                    ptr,
                    None,  # automatically assign key.
                    item_ptr))
                self._release_value(item_ptr)
        elif isinstance(python_value, dict):
            for key, value in python_value.items():
                if isinstance(key, unicode):
                    key = key.encode('utf-8')
                item_ptr = self.create_value(value)
                handle_return_value(unqlite_array_add_strkey_elem(
                    ptr,
                    key,
                    item_ptr))
                self._release_value(item_ptr)
        elif isinstance(python_value, (int, long)):
            unqlite_value_int(ptr, python_value)
        elif isinstance(python_value, bool):
            unqlite_value_bool(ptr, python_value)
        elif isinstance(python_value, float):
            unqlite_value_double(ptr, python_value)
        else:
            unqlite_value_null(ptr)

    def create_value(self, value):
        if isinstance(value, (list, tuple, dict)):
            ptr = self._create_array()
        else:
            ptr = self._create_scalar()
        self._set_value(ptr, value)
        return ptr

    def _release_value(self, ptr):
        raise NotImplementedError

    def _create_scalar(self):
        raise NotImplementedError

    def _create_array(self):
        raise NotImplementedError


class VM(_ValueBase):
    def __init__(self, unqlite):
        self._unqlite = unqlite
        self._vm = None
        self._ff_registry = {}

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
        for name in self._ff_registry.keys():
            self.delete_foreign_function(name)
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

    def _create_scalar(self):
        return unqlite_vm_new_scalar(self._vm)

    def _create_array(self):
        return unqlite_vm_new_array(self._vm)

    def _release_value(self, ptr):
        handle_return_value(unqlite_vm_release_value(self._vm, ptr))

    def set_value(self, name, value):
        ptr = self.create_value(value)
        self.config(UNQLITE_VM_CONFIG_CREATE_VAR, name, ptr)
        self._release_value(ptr)

    def extract(self, name):
        ptr = unqlite_vm_extract_variable(self._vm, name)
        try:
            return _convert_value(ptr)
        finally:
            self._release_value(ptr)

    def foreign_function(self, name, user_data=None):
        def _decorator(fn):
            c_callback, inner = wrap_foreign_function(fn)
            self._ff_registry[name] = c_callback
            unqlite_create_function(
                self._vm,
                name,
                c_callback,
                user_data or '')
            return inner
        return _decorator

    def delete_foreign_function(self, name):
        if name in self._ff_registry:
            del self._ff_registry[name]
        handle_return_value(unqlite_delete_function(self._vm, name))

    def __getitem__(self, name):
        return self.extract(name)

    def __setitem__(self, name, value):
        self.set_value(name, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._vm is not None:
            self.close()


class _Context(_ValueBase):
    def __init__(self, context):
        self._context = context

    def _create_scalar(self):
        return unqlite_context_new_scalar(self._context)

    def _create_array(self):
        return unqlite_context_new_array(self._context)

    def _release_value(self, ptr):
        unqlite_context_release_value(self._context, ptr)

    def push_result(self, value):
        ptr = self.create_value(value)
        unqlite_result_value(self._context, ptr)
        self._release_value(ptr)


class Collection(object):
    def __init__(self, unqlite, name):
        self.unqlite = unqlite
        self.name = name

    @contextmanager
    def _execute(self, script, **kwargs):
        with self.unqlite.compile_script(script) as vm:
            vm['collection'] = self.name
            for key, value in kwargs.items():
                vm[key] = value
            vm.execute()
            yield vm

    def _simple_execute(self, script, **kwargs):
        with self._execute(script, **kwargs) as vm:
            return vm['ret']

    def all(self):
        return self._simple_execute('$ret = db_fetch_all($collection);')

    def filter(self, filter_fn):
        script = '$ret = db_fetch_all($collection, _filter_func);'
        with self.unqlite.compile_script(script) as vm:
            @vm.foreign_function('_filter_func')
            def _filter_fn(context, obj):
                return filter_fn(obj)
            vm['collection'] = self.name
            vm.execute()
            ret = vm['ret']
            vm.delete_foreign_function('_filter_func')

        return ret

    def create(self):
        script = 'if (!db_exists($collection)) { db_create($collection); }'
        with self._execute(script) as vm:
            pass

    def drop(self):
        script = 'if (db_exists($collection)) { db_drop_collection($collection); }'
        with self._execute(script) as vm:
            pass

    def exists(self):
        return self._simple_execute('$ret = db_exists($collection);')

    def last_record_id(self):
        return self._simple_execute('$ret = db_last_record_id($collection);')

    def current_record_id(self):
        return self._simple_execute(
            '$ret = db_current_record_id($collection);')

    def reset_cursor(self):
        with self._execute('db_reset_record_cursor($collection);'):
            pass

    def __len__(self):
        return self._simple_execute('$ret = db_total_records($collection);')

    def delete(self, record_id):
        script = '$ret = db_drop_record($collection, $record_id);'
        return self._simple_execute(script, record_id=record_id)

    def fetch(self, record_id):
        script = '$ret = db_fetch_by_id($collection, $record_id);'
        return self._simple_execute(script, record_id=record_id)

    def store(self, record):
        script = '$ret = db_store($collection, $record);'
        return self._simple_execute(script, record=record)

    def update(self, record_id, record):
        script = '$ret = db_update_record($collection, $record_id, $record);'
        return self._simple_execute(script, record_id=record_id, record=record)

    def fetch_current(self):
        return self._simple_execute('$ret = db_fetch($collection);')

    __delitem__ = delete
    __getitem__ = fetch

    def error_log(self):
        return self._simple_execute('$ret = db_errlog();')


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
