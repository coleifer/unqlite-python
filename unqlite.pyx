# cython: language_level=3
# Python library for working with UnQLite databases.
#      _
#     /.)
#    /)\|
#   // /
#  /'" "
#
# "The bird a nest, the spider a web, man friendship.", William Blake.
#
# Thanks to buaabyl for pyUnQLite, whose source-code this library is based on.
# ASCII art designed by "pils".
from cpython.bytes cimport PyBytes_Check
from cpython.string cimport PyString_AsStringAndSize
from cpython.string cimport PyString_FromStringAndSize
from cpython.unicode cimport PyUnicode_AsUTF8String
from cpython.unicode cimport PyUnicode_Check
from libc.stdlib cimport free, malloc

import sys
try:
    from os import fsencode
except ImportError:
    try:
        from sys import getfilesystemencoding as _getfsencoding
    except ImportError:
        _fsencoding = 'utf-8'
    else:
        _fsencoding = _getfsencoding()
    fsencode = lambda s: s.encode(_fsencoding)

cdef extern from "src/unqlite.h":
    struct unqlite
    struct unqlite_kv_cursor

    # Jx9 types.
    ctypedef struct unqlite_vm
    ctypedef struct unqlite_context
    ctypedef struct unqlite_value

    # Simple types.
    ctypedef signed long long int sxi64
    ctypedef unsigned long long int sxu64
    ctypedef sxi64 unqlite_int64

    # Database.
    cdef int unqlite_open(unqlite **ppDb, const char *zFilename, unsigned int iMode)
    cdef int unqlite_config(unqlite *pDb, int nOp, ...)
    cdef int unqlite_close(unqlite *pDb)

    # Transactions.
    cdef int unqlite_begin(unqlite *pDb)
    cdef int unqlite_commit(unqlite *pDb)
    cdef int unqlite_rollback(unqlite *pDb)

    # Key/Value store.
    cdef int unqlite_kv_store(unqlite *pDb, const void *pKey, int nKeyLen, const void *pData, unqlite_int64 nDataLen)
    cdef int unqlite_kv_append(unqlite *pDb, const void *pKey, int nKeyLen, const void *pData, unqlite_int64 nDataLen)
    cdef int unqlite_kv_fetch(unqlite *pDb, const void *pKey, int nKeyLen, void *pBuf, unqlite_int64 *pSize)
    cdef int unqlite_kv_delete(unqlite *pDb, const void *pKey, int nKeyLen)
    cdef int unqlite_kv_config(unqlite *pDb, int iOp, ...)

    # Cursors.
    cdef int unqlite_kv_cursor_init(unqlite *pDb,unqlite_kv_cursor **ppOut)
    cdef int unqlite_kv_cursor_release(unqlite *pDb,unqlite_kv_cursor *pCur)
    cdef int unqlite_kv_cursor_seek(unqlite_kv_cursor *pCursor,const void *pKey,int nKeyLen,int iPos)
    cdef int unqlite_kv_cursor_first_entry(unqlite_kv_cursor *pCursor)
    cdef int unqlite_kv_cursor_last_entry(unqlite_kv_cursor *pCursor)
    cdef int unqlite_kv_cursor_valid_entry(unqlite_kv_cursor *pCursor)
    cdef int unqlite_kv_cursor_next_entry(unqlite_kv_cursor *pCursor)
    cdef int unqlite_kv_cursor_prev_entry(unqlite_kv_cursor *pCursor)
    cdef int unqlite_kv_cursor_key(unqlite_kv_cursor *pCursor,void *pBuf,int *pnByte)
    cdef int unqlite_kv_cursor_data(unqlite_kv_cursor *pCursor,void *pBuf,unqlite_int64 *pnData)
    cdef int unqlite_kv_cursor_delete_entry(unqlite_kv_cursor *pCursor)
    cdef int unqlite_kv_cursor_reset(unqlite_kv_cursor *pCursor)

    # Jx9.
    cdef int unqlite_compile(unqlite *pDb,const char *zJx9, int nByte, unqlite_vm **ppOut)
    cdef int unqlite_compile_file(unqlite *pDb,const char *zPath,unqlite_vm **ppOut)
    cdef int unqlite_vm_config(unqlite_vm *pVm,int iOp,...)
    cdef int unqlite_vm_exec(unqlite_vm *pVm)
    cdef int unqlite_vm_reset(unqlite_vm *pVm)
    cdef int unqlite_vm_release(unqlite_vm *pVm)
    cdef int unqlite_vm_dump(unqlite_vm *pVm, int (*xConsumer)(const void *, unsigned int, void *), void *pUserData)
    cdef unqlite_value * unqlite_vm_extract_variable(unqlite_vm *pVm,const char *zVarname)

    # Allocating variables.
    cdef unqlite_value * unqlite_vm_new_scalar(unqlite_vm *pVm)
    cdef unqlite_value * unqlite_vm_new_array(unqlite_vm *pVm)
    cdef int unqlite_vm_release_value(unqlite_vm *pVm,unqlite_value *pValue)
    cdef unqlite_value * unqlite_context_new_scalar(unqlite_context *pCtx)
    cdef unqlite_value * unqlite_context_new_array(unqlite_context *pCtx)
    cdef void unqlite_context_release_value(unqlite_context *pCtx,unqlite_value *pValue)

    # Dynamically-typed variables.
    cdef int unqlite_value_int(unqlite_value *pVal, int iValue)
    cdef int unqlite_value_int64(unqlite_value *pVal, unqlite_int64 iValue)
    cdef int unqlite_value_bool(unqlite_value *pVal, int iBool)
    cdef int unqlite_value_null(unqlite_value *pVal)
    cdef int unqlite_value_double(unqlite_value *pVal, double Value)
    cdef int unqlite_value_string(unqlite_value *pVal, const char *zString, int nLen)
    cdef int unqlite_value_string_format(unqlite_value *pVal, const char *zFormat,...)
    cdef int unqlite_value_reset_string_cursor(unqlite_value *pVal)
    cdef int unqlite_value_resource(unqlite_value *pVal, void *pUserData)
    cdef int unqlite_value_release(unqlite_value *pVal)

    # Foreign function parameter values.
    cdef int unqlite_value_to_int(unqlite_value *pValue)
    cdef int unqlite_value_to_bool(unqlite_value *pValue)
    cdef unqlite_int64 unqlite_value_to_int64(unqlite_value *pValue)
    cdef double unqlite_value_to_double(unqlite_value *pValue)
    cdef const char * unqlite_value_to_string(unqlite_value *pValue, int *pLen)
    cdef void * unqlite_value_to_resource(unqlite_value *pValue)
    cdef int unqlite_value_compare(unqlite_value *pLeft, unqlite_value *pRight, int bStrict)

    # Foreign function results.
    cdef int unqlite_result_int(unqlite_context *pCtx, int iValue)
    cdef int unqlite_result_int64(unqlite_context *pCtx, unqlite_int64 iValue)
    cdef int unqlite_result_bool(unqlite_context *pCtx, int iBool)
    cdef int unqlite_result_double(unqlite_context *pCtx, double Value)
    cdef int unqlite_result_null(unqlite_context *pCtx)
    cdef int unqlite_result_string(unqlite_context *pCtx, const char *zString, int nLen)
    cdef int unqlite_result_string_format(unqlite_context *pCtx, const char *zFormat, ...)
    cdef int unqlite_result_value(unqlite_context *pCtx, unqlite_value *pValue)
    cdef int unqlite_result_resource(unqlite_context *pCtx, void *pUserData)

    # Object reflection.
    cdef int unqlite_value_is_int(unqlite_value *pVal)
    cdef int unqlite_value_is_float(unqlite_value *pVal)
    cdef int unqlite_value_is_bool(unqlite_value *pVal)
    cdef int unqlite_value_is_string(unqlite_value *pVal)
    cdef int unqlite_value_is_null(unqlite_value *pVal)
    cdef int unqlite_value_is_numeric(unqlite_value *pVal)
    cdef int unqlite_value_is_callable(unqlite_value *pVal)
    cdef int unqlite_value_is_scalar(unqlite_value *pVal)
    cdef int unqlite_value_is_json_array(unqlite_value *pVal)
    cdef int unqlite_value_is_json_object(unqlite_value *pVal)
    cdef int unqlite_value_is_resource(unqlite_value *pVal)
    cdef int unqlite_value_is_empty(unqlite_value *pVal)

    # JSON Array/Object Management Interfaces
    cdef unqlite_value * unqlite_array_fetch(unqlite_value *pArray, const char *zKey, int nByte)
    cdef int unqlite_array_walk(unqlite_value *pArray, int (*xWalk)(unqlite_value *, unqlite_value *, void *), void *pUserData)
    cdef int unqlite_array_add_elem(unqlite_value *pArray, unqlite_value *pKey, unqlite_value *pValue)
    cdef int unqlite_array_add_strkey_elem(unqlite_value *pArray, const char *zKey, unqlite_value *pValue)
    cdef int unqlite_array_count(unqlite_value *pArray)

    # Call Context Handling Interfaces
    cdef int unqlite_context_output(unqlite_context *pCtx, const char *zString, int nLen)
    cdef int unqlite_context_output_format(unqlite_context *pCtx,const char *zFormat, ...)
    cdef int unqlite_context_throw_error(unqlite_context *pCtx, int iErr, const char *zErr)
    cdef int unqlite_context_throw_error_format(unqlite_context *pCtx, int iErr, const char *zFormat, ...)
    cdef unsigned int unqlite_context_random_num(unqlite_context *pCtx)
    cdef int unqlite_context_random_string(unqlite_context *pCtx, char *zBuf, int nBuflen)
    cdef void * unqlite_context_user_data(unqlite_context *pCtx)
    cdef int unqlite_context_push_aux_data(unqlite_context *pCtx, void *pUserData)
    cdef void * unqlite_context_peek_aux_data(unqlite_context *pCtx)
    cdef unsigned int unqlite_context_result_buf_length(unqlite_context *pCtx)
    cdef const char * unqlite_function_name(unqlite_context *pCtx)

    # Foreign functions.
    cdef int unqlite_create_function(unqlite_vm *pVm,const char *zName,int (*xFunc)(unqlite_context *,int,unqlite_value **),void *pUserData)
    cdef int unqlite_delete_function(unqlite_vm *pVm, const char *zName)

    # Misc utils.
    cdef int unqlite_util_random_string(unqlite *pDb, char *zBuf, unsigned int buf_size)
    cdef unsigned int unqlite_util_random_num(unqlite *pDb)

    # Library info.
    cdef const char * unqlite_lib_version()

    # Constant values (http://unqlite.org/c_api_const.html).
    cdef int SXRET_OK = 0
    cdef int SXERR_MEM = -1
    cdef int SXERR_IO = -2
    cdef int SXERR_EMPTY = -3
    cdef int SXERR_LOCKED = -4
    cdef int SXERR_ORANGE = -5
    cdef int SXERR_NOTFOUND = -6
    cdef int SXERR_LIMIT = -7
    cdef int SXERR_MORE = -8
    cdef int SXERR_INVALID = -9
    cdef int SXERR_ABORT = -10
    cdef int SXERR_EXISTS = -11
    cdef int SXERR_SYNTAX = -12
    cdef int SXERR_UNKNOWN = -13
    cdef int SXERR_BUSY = -14
    cdef int SXERR_OVERFLOW = -15
    cdef int SXERR_WILLBLOCK = -16
    cdef int SXERR_NOTIMPLEMENTED = -17
    cdef int SXERR_EOF = -18
    cdef int SXERR_PERM = -19
    cdef int SXERR_NOOP = -20
    cdef int SXERR_FORMAT = -21
    cdef int SXERR_NEXT = -22
    cdef int SXERR_OS = -23
    cdef int SXERR_CORRUPT = -24
    cdef int SXERR_CONTINUE = -25
    cdef int SXERR_NOMATCH = -26
    cdef int SXERR_RESET = -27
    cdef int SXERR_DONE = -28
    cdef int SXERR_SHORT = -29
    cdef int SXERR_PATH = -30
    cdef int SXERR_TIMEOUT = -31
    cdef int SXERR_BIG = -32
    cdef int SXERR_RETRY = -33
    cdef int SXERR_IGNORE = -63

    # UnQLite return values and error codes.
    cdef int UNQLITE_OK = SXRET_OK
    cdef int UNQLITE_NOMEM = SXERR_MEM
    cdef int UNQLITE_ABORT = SXERR_ABORT
    cdef int UNQLITE_IOERR = SXERR_IO
    cdef int UNQLITE_CORRUPT = SXERR_CORRUPT
    cdef int UNQLITE_LOCKED = SXERR_LOCKED
    cdef int UNQLITE_BUSY = SXERR_BUSY
    cdef int UNQLITE_DONE = SXERR_DONE
    cdef int UNQLITE_PERM = SXERR_PERM
    cdef int UNQLITE_NOTIMPLEMENTED = SXERR_NOTIMPLEMENTED
    cdef int UNQLITE_NOTFOUND = SXERR_NOTFOUND
    cdef int UNQLITE_NOOP = SXERR_NOOP
    cdef int UNQLITE_INVALID = SXERR_INVALID
    cdef int UNQLITE_EOF = SXERR_EOF
    cdef int UNQLITE_UNKNOWN = SXERR_UNKNOWN
    cdef int UNQLITE_LIMIT = SXERR_LIMIT
    cdef int UNQLITE_EXISTS = SXERR_EXISTS
    cdef int UNQLITE_EMPTY = SXERR_EMPTY
    cdef int UNQLITE_COMPILE_ERR = -70
    cdef int UNQLITE_VM_ERR = -71
    cdef int UNQLITE_FULL = -73
    cdef int UNQLITE_CANTOPEN = -74
    cdef int UNQLITE_READ_ONLY = -75
    cdef int UNQLITE_LOCKERR = -76

    # Database config commands.
    cdef int UNQLITE_CONFIG_JX9_ERR_LOG = 1
    cdef int UNQLITE_CONFIG_MAX_PAGE_CACHE = 2
    cdef int UNQLITE_CONFIG_ERR_LOG = 3
    cdef int UNQLITE_CONFIG_KV_ENGINE = 4
    cdef int UNQLITE_CONFIG_DISABLE_AUTO_COMMIT = 5
    cdef int UNQLITE_CONFIG_GET_KV_NAME = 6

    # Open mode flags.
    cdef int UNQLITE_OPEN_READONLY = 0x00000001
    cdef int UNQLITE_OPEN_READWRITE = 0x00000002
    cdef int UNQLITE_OPEN_CREATE = 0x00000004
    cdef int UNQLITE_OPEN_EXCLUSIVE = 0x00000008
    cdef int UNQLITE_OPEN_TEMP_DB = 0x00000010
    cdef int UNQLITE_OPEN_NOMUTEX = 0x00000020
    cdef int UNQLITE_OPEN_OMIT_JOURNALING = 0x00000040
    cdef int UNQLITE_OPEN_IN_MEMORY = 0x00000080
    cdef int UNQLITE_OPEN_MMAP = 0x00000100

    # Cursor seek flags.
    cdef int UNQLITE_CURSOR_MATCH_EXACT = 1
    cdef int UNQLITE_CURSOR_MATCH_LE = 2
    cdef int UNQLITE_CURSOR_MATCH_GE = 3

    # VM config commands.
    cdef int UNQLITE_VM_CONFIG_OUTPUT = 1  # TWO ARGUMENTS: int (*xConsumer)(const void *pOut, unsigned int nLen, void *pUserData), void *pUserData
    cdef int UNQLITE_VM_CONFIG_IMPORT_PATH = 2  # ONE ARGUMENT: const char *zIncludePath
    cdef int UNQLITE_VM_CONFIG_ERR_REPORT = 3  # NO ARGUMENTS: Report all run-time errors in the VM output
    cdef int UNQLITE_VM_CONFIG_RECURSION_DEPTH = 4  # ONE ARGUMENT: int nMaxDepth
    cdef int UNQLITE_VM_OUTPUT_LENGTH = 5  # ONE ARGUMENT: unsigned int *pLength
    cdef int UNQLITE_VM_CONFIG_CREATE_VAR = 6  # TWO ARGUMENTS: const char *zName, unqlite_value *pValue
    cdef int UNQLITE_VM_CONFIG_HTTP_REQUEST = 7  # TWO ARGUMENTS: const char *zRawRequest, int nRequestLength
    cdef int UNQLITE_VM_CONFIG_SERVER_ATTR = 8  # THREE ARGUMENTS: const char *zKey, const char *zValue, int nLen
    cdef int UNQLITE_VM_CONFIG_ENV_ATTR = 9  # THREE ARGUMENTS: const char *zKey, const char *zValue, int nLen
    cdef int UNQLITE_VM_CONFIG_EXEC_VALUE = 10  # ONE ARGUMENT: unqlite_value **ppValue
    cdef int UNQLITE_VM_CONFIG_IO_STREAM = 11  # ONE ARGUMENT: const unqlite_io_stream *pStream
    cdef int UNQLITE_VM_CONFIG_ARGV_ENTRY = 12  # ONE ARGUMENT: const char *zValue
    cdef int UNQLITE_VM_CONFIG_EXTRACT_OUTPUT = 13  # TWO ARGUMENTS: const void **ppOut, unsigned int *pOutputLen


cdef inline unicode decode(key):
    cdef unicode ukey
    if PyBytes_Check(key):
        ukey = key.decode('utf-8')
    elif PyUnicode_Check(key):
        ukey = <unicode>key
    elif key is None:
        return None
    else:
        ukey = unicode(key)
    return ukey

cdef inline bytes encode(key):
    cdef bytes bkey
    if PyUnicode_Check(key):
        bkey = PyUnicode_AsUTF8String(key)
    elif PyBytes_Check(key):
        bkey = <bytes>key
    elif key is None:
        return None
    else:
        bkey = PyUnicode_AsUTF8String(unicode(key))
    return bkey


cdef dict EXC_MAP = {
    UNQLITE_NOMEM: MemoryError,
    UNQLITE_NOTIMPLEMENTED: NotImplementedError,
    UNQLITE_NOTFOUND: KeyError,
    UNQLITE_NOOP: NotImplementedError,
}


class UnQLiteError(Exception):
    def __init__(self, msg, errno):
        self.errno = errno
        self.error_message = msg
        super(UnQLiteError, self).__init__(msg)

    def __repr__(self):
        return '<UnQLiteError %s: %s>' % (self.errno, self.error_message)


cdef class UnQLite(object):
    """
    UnQLite database wrapper.
    """
    cdef unqlite *database
    cdef readonly bint is_memory
    cdef readonly bint is_open
    cdef readonly basestring filename
    cdef readonly bytes encoded_filename
    cdef readonly int flags
    cdef bint open_database

    def __cinit__(self):
        self.database = <unqlite *>0
        self.is_memory = False
        self.is_open = False

    def __dealloc__(self):
        if self.is_open:
            unqlite_close(self.database)

    def __init__(self, filename=':mem:', flags=UNQLITE_OPEN_CREATE,
                 open_database=True):
        self.filename = filename
        if isinstance(filename, unicode):
            self.encoded_filename = fsencode(filename)
        else:
            self.encoded_filename = encode(filename)
        self.flags = flags
        self.is_memory = self.encoded_filename == b':mem:'
        self.open_database = open_database
        if self.open_database:
            self.open()

    def open(self):
        """Open database connection."""
        cdef int ret

        if self.is_open: return False

        self.check_call(unqlite_open(
            &self.database,
            self.encoded_filename,
            self.flags))

        self.is_open = True
        return True

    def close(self):
        """Close database connection."""
        if not self.is_open: return False

        self.check_call(unqlite_close(self.database))
        self.is_open = False
        self.database = <unqlite *>0
        return True

    def __enter__(self):
        """Use database connection as a context manager."""
        if not self.is_open:
            self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    cpdef disable_autocommit(self):
        if self.is_memory: return False

        # Disable autocommit for file-based databases.
        ret = unqlite_config(
            self.database,
            UNQLITE_CONFIG_DISABLE_AUTO_COMMIT)
        if ret != UNQLITE_OK:
            raise NotImplementedError('Error disabling autocommit for '
                                      'in-memory database.')
        return True

    cpdef store(self, key, value):
        """Store key/value."""
        cdef bytes encoded_key = encode(key)
        cdef bytes encoded_value = encode(value)

        self.check_call(unqlite_kv_store(
            self.database,
            <const char *>encoded_key,
            -1,
            <const char *>encoded_value,
            len(encoded_value)))

    cpdef fetch(self, key):
        """Retrieve value at given key. Raises `KeyError` if key not found."""
        cdef char *buf = <char *>0
        cdef unqlite_int64 buf_size = 0
        cdef bytes encoded_key = encode(key)

        self.check_call(unqlite_kv_fetch(
            self.database,
            <const char *>encoded_key,
            -1,
            <void *>0,
            &buf_size))

        try:
            buf = <char *>malloc(buf_size)
            self.check_call(unqlite_kv_fetch(
                self.database,
                <const char *>encoded_key,
                -1,
                <void *>buf,
                &buf_size))
            value = buf[:buf_size]
            return value
        finally:
            free(buf)

    cpdef delete(self, key):
        """Delete the value stored at the given key."""
        cdef bytes encoded_key = encode(key)

        self.check_call(unqlite_kv_delete(
            self.database, <char *>encoded_key, -1))

    cpdef append(self, key, value):
        """Append to the value stored in the given key."""
        cdef bytes encoded_key = encode(key)
        cdef bytes encoded_value = encode(value)

        self.check_call(unqlite_kv_append(
            self.database,
            <const char *>encoded_key,
            -1,
            <const char *>encoded_value,
            len(encoded_value)))

    cpdef exists(self, key):
        cdef bytes encoded_key = encode(key)
        cdef char *buf = <char *>0
        cdef unqlite_int64 buf_size = 0
        cdef int ret

        ret = unqlite_kv_fetch(
            self.database,
            <const char *>encoded_key,
            -1,
            <void *>0,
            &buf_size)
        if ret == UNQLITE_NOTFOUND:
            return False
        elif ret == UNQLITE_OK:
            return True

        raise self._build_exception_for_error(ret)

    def __setitem__(self, key, value):
        self.store(key, value)

    def __getitem__(self, key):
        return self.fetch(key)

    def __delitem__(self, key):
        self.delete(key)

    def __contains__(self, key):
        return self.exists(key)

    cdef check_call(self, int result):
        """
        Check for a successful UnQLite library call, raising an exception
        if the result is other than `UNQLITE_OK`.
        """
        if result != UNQLITE_OK:
            raise self._build_exception_for_error(result)

    cdef _build_exception_for_error(self, int status):
        cdef bytes message

        if status == UNQLITE_NOTFOUND:
            message = b'key not found'
        else:
            message = self._get_last_error()

        if status in EXC_MAP:
            return EXC_MAP[status](message.decode('utf8'))
        else:
            return UnQLiteError(message.decode('utf8'), status)

    cdef _get_last_error(self):
        cdef int ret
        cdef int size
        cdef char *zBuf

        ret = unqlite_config(
            self.database,
            UNQLITE_CONFIG_ERR_LOG,
            &zBuf,
            &size)
        if ret != UNQLITE_OK or size == 0:
            return None

        return zBuf[:size]

    cpdef begin(self):
        """Begin a new transaction. Only works for file-based databases."""
        if self.is_memory: return False

        self.check_call(unqlite_begin(self.database))
        return True

    cpdef commit(self):
        """Commit current transaction. Only works for file-based databases."""
        if self.is_memory: return False

        self.check_call(unqlite_commit(self.database))
        return True

    cpdef rollback(self):
        """Rollback current transaction. Only works for file-based databases."""
        if self.is_memory: return False

        self.check_call(unqlite_rollback(self.database))
        return True

    def transaction(self):
        """Create context manager for wrapping a transaction."""
        return Transaction(self)

    def commit_on_success(self, fn):
        def wrapper(*args, **kwargs):
            with self.transaction():
                return fn(*args, **kwargs)
        return wrapper

    def cursor(self):
        """Create a cursor for iterating through the database."""
        return Cursor(self)

    def vm(self, code):
        """Create an UnQLite Jx9 virtual machine."""
        return VM(self, code)

    def collection(self, name):
        """Create a wrapper for working with Jx9 collections."""
        return Collection(self, name)

    cpdef update(self, dict values):
        for key in values:
            self.store(key, values[key])

    def keys(self):
        """Efficiently iterate through the database's keys."""
        cdef Cursor cursor
        with self.cursor() as cursor:
            while cursor.is_valid():
                yield cursor.key()
                try:
                    cursor.next_entry()
                except StopIteration:
                    break

    def values(self):
        """Efficiently iterate through the database's values."""
        cdef Cursor cursor
        with self.cursor() as cursor:
            while cursor.is_valid():
                yield cursor.value()
                try:
                    cursor.next_entry()
                except StopIteration:
                    break

    def items(self):
        """Efficiently iterate through the database's key/value pairs."""
        cdef Cursor cursor
        cdef tuple item

        with self.cursor() as cursor:
            for item in cursor:
                yield item

    def __iter__(self):
        cursor = self.cursor()
        cursor.reset()
        return cursor

    def range(self, start_key, end_key,
                bint include_end_key=True):
        cdef Cursor cursor = self.cursor()
        try:
            cursor.seek(start_key)
        except KeyError:
            pass
        else:
            for item in cursor.fetch_until(end_key, include_end_key):
                yield item

    def __len__(self):
        """
        Return the total number of records in the database.

        Note: this operation is O(n) and requires iterating through the
        entire key-space.
        """
        cdef Cursor cursor
        cdef long count = 0
        with self.cursor() as cursor:
            for item in cursor:
                count += 1
        return count

    def flush(self):
        """
        Remove all records from the database.

        Note: this operation is O(n) and requires iterating through the
        entire key-space.
        """
        cdef Cursor cursor
        cdef long i = 0
        with self.cursor() as cursor:
            while cursor.is_valid():
                cursor.delete()
                i += 1
        return i

    cpdef random_string(self, int nbytes):
        """Generate a random string of given length."""
        cdef char *buf
        buf = <char *>malloc(nbytes * sizeof(char))
        try:
            unqlite_util_random_string(self.database, buf, nbytes)
            return bytes(buf[:nbytes])
        finally:
            free(buf)

    cpdef int random_int(self):
        """Generate a random integer."""
        return unqlite_util_random_num(self.database)

    def lib_version(self):
        return unqlite_lib_version()


cdef class Transaction(object):
    """Expose transaction as a context manager."""
    cdef UnQLite unqlite

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
            except Exception:
                self.unqlite.rollback()
                raise


cdef class Cursor(object):
    """Cursor interface for efficiently iterating through database."""
    cdef UnQLite unqlite
    cdef unqlite_kv_cursor *cursor
    cdef bint consumed

    def __cinit__(self, unqlite):
        self.unqlite = unqlite
        self.cursor = <unqlite_kv_cursor *>0
        unqlite_kv_cursor_init(self.unqlite.database, &self.cursor)

    def __dealloc__(self):
        unqlite_kv_cursor_release(self.unqlite.database, self.cursor)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    cpdef reset(self):
        """Reset the cursor's position."""
        unqlite_kv_cursor_reset(self.cursor)

    cpdef seek(self, key, int flags=UNQLITE_CURSOR_MATCH_EXACT):
        """
        Seek to the given key. The flags specify how UnQLite will determine
        when to stop. Values are:

        * UNQLITE_CURSOR_MATCH_EXACT (default).
        * UNQLITE_CURSOR_MATCH_LE
        * UNQLITE_CURSOR_MATCH_GE
        """
        cdef bytes encoded_key = encode(key)

        self.unqlite.check_call(unqlite_kv_cursor_seek(
            self.cursor,
            <char *>encoded_key,
            -1,
            flags))

    cpdef first(self):
        """Set cursor to the first record in the database."""
        self.unqlite.check_call(unqlite_kv_cursor_first_entry(self.cursor))

    cpdef last(self):
        """Set cursor to the last record in the database."""
        self.unqlite.check_call(unqlite_kv_cursor_last_entry(self.cursor))

    cpdef next_entry(self):
        """Move cursor to the next entry."""
        cdef int ret
        ret = unqlite_kv_cursor_next_entry(self.cursor)
        if ret != UNQLITE_OK:
            raise StopIteration

    cpdef previous_entry(self):
        """Move cursor to the previous entry."""
        cdef int ret
        ret = unqlite_kv_cursor_prev_entry(self.cursor)
        if ret != UNQLITE_OK:
            raise StopIteration

    cpdef bint is_valid(self):
        """
        Return a boolean value indicating whether the cursor is currently
        pointing to a valid record.
        """
        if unqlite_kv_cursor_valid_entry(self.cursor):
            return True
        return False

    def __iter__(self):
        self.consumed = False
        return self

    cpdef key(self):
        """Retrieve the key at the cursor's current location."""
        cdef char *buf
        cdef int buf_size

        self.unqlite.check_call(
            unqlite_kv_cursor_key(self.cursor, <void *>0, &buf_size))

        try:
            buf = <char *>malloc(buf_size * sizeof(char))
            unqlite_kv_cursor_key(
                self.cursor,
                <char *>buf,
                &buf_size)

            key = buf[:buf_size]
            try:
                return key.decode('utf-8')
            except UnicodeDecodeError:
                return key
        finally:
            free(buf)

    cpdef value(self):
        """Retrieve the value at the cursor's current location."""
        cdef char *buf
        cdef unqlite_int64 buf_size

        self.unqlite.check_call(
            unqlite_kv_cursor_data(self.cursor, <void *>0, &buf_size))

        try:
            buf = <char *>malloc(buf_size * sizeof(char))
            unqlite_kv_cursor_data(
                self.cursor,
                <char *>buf,
                &buf_size)

            value = buf[:buf_size]
            return value
        finally:
            free(buf)

    cpdef delete(self):
        """Delete the record at the cursor's current location."""
        self.unqlite.check_call(unqlite_kv_cursor_delete_entry(self.cursor))

    def __next__(self):
        cdef int ret

        if self.consumed:
            raise StopIteration

        try:
            key = self.key()
            value = self.value()
        except Exception:
            raise StopIteration
        else:
            ret = unqlite_kv_cursor_next_entry(self.cursor)
            if ret != UNQLITE_OK:
                self.consumed = True

        return (key, value)

    def fetch_until(self, stop_key, bint include_stop_key=True):
        for key, value in self:
            if key == stop_key:
                if include_stop_key:
                    yield (key, value)
                raise StopIteration
            else:
                yield (key, value)


# Foreign function callback signature.
ctypedef int (*unqlite_filter_fn)(unqlite_context *, int, unqlite_value **)


cdef class VM(object):
    """Jx9 virtual-machine interface."""
    cdef UnQLite unqlite
    cdef unqlite_vm *vm
    cdef readonly bint need_reset
    cdef readonly code
    cdef readonly bytes encoded_code
    cdef set encoded_names

    def __cinit__(self, UnQLite unqlite, code):
        self.unqlite = unqlite
        self.vm = <unqlite_vm *>0
        self.code = code
        self.encoded_code = encode(code)
        self.encoded_names = set()

    def __dealloc__(self):
        # For some reason, calling unqlite_vm_release() here always causes a
        # segfault.
        pass

    cpdef compile(self):
        """Compile the Jx9 script."""
        self.encoded_names.clear()
        self.unqlite.check_call(unqlite_compile(
            self.unqlite.database,
            <const char *>self.encoded_code,
            -1,
            &self.vm))

    cpdef execute(self):
        """Execute the compiled Jx9 script."""
        if not self.vm:
            raise UnQLiteError('Jx9 script must be compiled before executing.')

        self.unqlite.check_call(unqlite_vm_exec(self.vm))

    cpdef reset(self):
        if not self.vm:
            raise UnQLiteError('Jx9 script has not been compiled.')

        self.unqlite.check_call(unqlite_vm_reset(self.vm))
        return True

    cpdef close(self):
        """Close and release the virtual machine."""
        self.encoded_names.clear()
        if self.vm:
            unqlite_vm_release(self.vm)
            self.vm = <unqlite_vm *>0

    def __enter__(self):
        self.compile()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    cdef unqlite_value* create_value(self, value):
        """
        Create an `unqlite_value` corresponding to the given Python value.
        """
        cdef unqlite_value *ptr
        if isinstance(value, (list, tuple, dict)):
            ptr = self.create_array()
        else:
            ptr = self.create_scalar()
        python_to_unqlite_value(self, ptr, value)
        return ptr

    cdef release_value(self, unqlite_value *ptr):
        """Release the given `unqlite_value`."""
        self.unqlite.check_call(unqlite_vm_release_value(self.vm, ptr))

    cdef unqlite_value* create_array(self):
        return unqlite_vm_new_array(self.vm)

    cdef unqlite_value* create_scalar(self):
        return unqlite_vm_new_scalar(self.vm)

    def set_value(self, name, value):
        """Set the value of a variable in the Jx9 script."""
        cdef unqlite_value *ptr
        cdef bytes encoded_name = encode(name)

        # since Jx9 does not make a private copy of the name,
        # we need to keep it alive by adding it to a set
        self.encoded_names.add(encoded_name)

        ptr = self.create_value(value)
        self.unqlite.check_call(unqlite_vm_config(
            self.vm,
            UNQLITE_VM_CONFIG_CREATE_VAR,
            <const char *>encoded_name,
            ptr))
        # since Jx9 makes a private copy of the value,
        # we do not need to keep the value alive
        self.release_value(ptr)

    def get_value(self, name):
        """
        Retrieve the value of a variable after the execution of the
        Jx9 script.
        """
        cdef unqlite_value *ptr
        cdef bytes encoded_name = encode(name)

        ptr = unqlite_vm_extract_variable(self.vm, <const char *>encoded_name)
        if not ptr:
            raise KeyError(name)
        try:
            return unqlite_value_to_python(ptr)
        finally:
            self.release_value(ptr)

    def __getitem__(self, name):
        return self.get_value(name)

    def __setitem__(self, name, value):
        self.set_value(name, value)

    cpdef set_values(self, dict data):
        for key, value in data.items():
            self.set_value(key, value)


cdef class Context(object):
    cdef unqlite_context *context

    def __cinit__(self):
        self.context = NULL

    cdef set_context(self, unqlite_context *context):
        self.context = context

    cdef unqlite_value * create_value(self, value):
        cdef unqlite_value *ptr

        if isinstance(value, (list, tuple, dict)):
            ptr = self.create_array()
        else:
            ptr = self.create_scalar()

        self.python_to_unqlite_value(ptr, value)
        return ptr

    cdef release_value(self, unqlite_value *ptr):
        unqlite_context_release_value(self.context, ptr)

    cdef unqlite_value* create_array(self):
        return unqlite_context_new_array(self.context)

    cdef unqlite_value* create_scalar(self):
        return unqlite_context_new_scalar(self.context)

    cpdef push_result(self, value):
        cdef unqlite_value *ptr
        ptr = self.create_value(value)
        unqlite_result_value(self.context, ptr)
        self.release_value(ptr)

    cdef python_to_unqlite_value(self, unqlite_value *ptr, python_value):
        cdef unqlite_value *item_ptr = <unqlite_value *>0
        cdef bytes encoded_value

        if isinstance(python_value, unicode):
            encoded_value = encode(python_value)
            unqlite_value_string(ptr, encoded_value, -1)
        elif isinstance(python_value, bytes):
            unqlite_value_string(ptr, python_value, -1)
        elif isinstance(python_value, (list, tuple)):
            for item in python_value:
                item_ptr = self.create_value(item)
                unqlite_array_add_elem(ptr, NULL, item_ptr)
                self.release_value(item_ptr)
        elif isinstance(python_value, dict):
            for key, value in python_value.items():
                encoded_value = encode(key)
                item_ptr = self.create_value(value)
                unqlite_array_add_strkey_elem(
                    ptr,
                    <const char *>encoded_value,
                    item_ptr)
                self.release_value(item_ptr)
        elif isinstance(python_value, bool):
            unqlite_value_bool(ptr, python_value)
        elif isinstance(python_value, (int, long)):
            unqlite_value_int64(ptr, python_value)
        elif isinstance(python_value, float):
            unqlite_value_double(ptr, python_value)
        else:
            unqlite_value_null(ptr)


cdef int py_filter_wrapper(unqlite_context *context, int nargs, unqlite_value **values):
    cdef int i
    cdef list converted = []
    cdef object callback = <object>unqlite_context_user_data(context)
    cdef Context context_wrapper = Context()

    context_wrapper.set_context(context)

    for i in range(nargs):
        converted.append(unqlite_value_to_python(values[i]))

    try:
        ret = callback(*converted)
    except KeyError:
        context_wrapper.push_result(False)
    except Exception:
        return UNQLITE_ABORT
    else:
        context_wrapper.push_result(ret)
    return UNQLITE_OK


cdef class Collection(object):
    """
    Manage collections of UnQLite JSON documents.
    """
    cdef UnQLite unqlite
    cdef basestring name

    def __init__(self, UnQLite unqlite, basestring name):
        self.unqlite = unqlite
        self.name = decode(name)

    def _execute(self, basestring script, **kwargs):
        cdef VM vm
        with VM(self.unqlite, script) as vm:
            vm['collection'] = self.name
            vm.set_values(kwargs)
            vm.execute()

    def _simple_execute(self, basestring script, **kwargs):
        cdef VM vm
        with VM(self.unqlite, script) as vm:
            vm['collection'] = self.name
            vm.set_values(kwargs)
            vm.execute()
            try:
                return vm['ret']
            except KeyError:
                raise ValueError('Error fetching return value from script.')

    def all(self):
        """Retrieve all records in the given collection."""
        return self._simple_execute('$ret = db_fetch_all($collection);')

    cpdef filter(self, filter_fn):
        """
        Filter the records in the collection using the provided Python
        callback.
        """
        cdef unqlite_filter_fn filter_callback = py_filter_wrapper
        cdef VM vm
        cdef void *cb_pointer = <void *>filter_fn

        script = '$ret = db_fetch_all($collection, _filter_fn)'
        with VM(self.unqlite, script) as vm:
            unqlite_create_function(
                vm.vm,
                '_filter_fn',
                filter_callback,
                cb_pointer)
            vm['collection'] = self.name
            vm.execute()
            ret = vm['ret']
            unqlite_delete_function(
                vm.vm,
                '_filter_fn')

        return ret

    def create(self):
        """
        Create the named collection.

        Note: this does not create a new JSON document, this method is
        used to create the collection itself.
        """
        return self._simple_execute('if (!db_exists($collection)) { '
                                    '$ret = db_create($collection); } '
                                    'else { $ret = false; }')

    def drop(self):
        """Drop the collection and all associated records."""
        return self._simple_execute('if (db_exists($collection)) { '
                                    '$ret = db_drop_collection($collection); }'
                                    'else { $ret = false; }')

    def exists(self):
        """Return boolean indicating whether the collection exists."""
        return self._simple_execute('$ret = db_exists($collection);')

    def last_record_id(self):
        """Return the ID of the last document to be stored."""
        return self._simple_execute('$ret = db_last_record_id($collection);')

    def current_record_id(self):
        """Return the ID of the current JSON document."""
        return self._simple_execute(
            '$ret = db_current_record_id($collection);')

    def reset_cursor(self):
        self._execute('db_reset_record_cursor($collection);')

    def creation_date(self):
        return self._simple_execute('$ret = db_creation_date($collection);')

    def set_schema(self, _schema=None, **kwargs):
        schema = _schema or {}
        if kwargs: schema.update(kwargs)
        return self._simple_execute(
            '$ret = db_set_schema($collection, $schema);', schema=schema)

    def get_schema(self):
        return self._simple_execute('$ret = db_get_schema($collection);')

    def __len__(self):
        """Return the number of records in the document collection."""
        return self._simple_execute('$ret = db_total_records($collection);')

    def delete(self, record_id):
        """Delete the document associated with the given ID."""
        script = '$ret = db_drop_record($collection, $record_id);'
        return self._simple_execute(script, record_id=record_id)

    def fetch(self, record_id):
        """Fetch the document associated with the given ID."""
        script = '$ret = db_fetch_by_id($collection, $record_id);'
        return self._simple_execute(script, record_id=record_id)

    def store(self, record, return_id=True):
        """
        Create a new JSON document in the collection, optionally returning
        the new record's ID.
        """
        if return_id:
            script = ('if (db_store($collection, $record)) { '
                      '$ret = db_last_record_id($collection); }')
        else:
            script = '$ret = db_store($collection, $record);'
        return self._simple_execute(script, record=record)

    def update(self, record_id, record):
        """
        Update the record identified by the given ID.
        """
        script = '$ret = db_update_record($collection, $record_id, $record);'
        return self._simple_execute(script, record_id=record_id, record=record)

    def fetch_current(self):
        return self._simple_execute('$ret = db_fetch($collection);')

    def __delitem__(self, record_id):
        self.delete(record_id)

    def __getitem__(self, record_id):
        return self.fetch(record_id)

    def __setitem__(self, record_id, record):
        self.update(record_id, record)

    def error_log(self):
        return self._simple_execute('$ret = db_errlog();')

    def iterator(self):
        return CollectionIterator(self)

    def __iter__(self):
        return iter(CollectionIterator(self))


cdef class CollectionIterator(object):
    cdef:
        VM vm
        UnQLite unqlite
        bint done
        public Collection collection

    def __init__(self, Collection collection):
        self.collection = collection
        self.unqlite = self.collection.unqlite
        self.vm = None
        self.done = True

    def __iter__(self):
        if self.vm is not None:
            self.vm.close()

        script = '$row = db_fetch($collection)'
        self.vm = VM(self.unqlite, script)
        self.vm.compile()
        self.vm['collection'] = self.collection.name
        self.done = False
        return self

    def __next__(self):
        if self.done:
            raise StopIteration

        self.vm.execute()
        row = self.vm['row']
        if row is None:
            self.done = True
            self.vm.close()
            self.vm = None
            raise StopIteration

        self.vm.reset()
        return row


cdef unqlite_value_to_python(unqlite_value *ptr):
    cdef list json_array
    cdef dict json_object

    if unqlite_value_is_json_object(ptr):
        json_object = {}
        unqlite_array_walk(
            ptr,
            unqlite_value_to_dict,
            <void *>json_object)
        return json_object
    elif unqlite_value_is_json_array(ptr):
        json_array = []
        unqlite_array_walk(
            ptr,
            unqlite_value_to_list,
            <void *>json_array)
        return json_array
    elif unqlite_value_is_string(ptr):
        bytestring = unqlite_value_to_string(ptr, NULL)
        try:
            return decode(bytestring)
        except UnicodeDecodeError:
            return bytestring
    elif unqlite_value_is_int(ptr):
        return unqlite_value_to_int64(ptr)
    elif unqlite_value_is_float(ptr):
        return unqlite_value_to_double(ptr)
    elif unqlite_value_is_bool(ptr):
        return bool(unqlite_value_to_bool(ptr))
    elif unqlite_value_is_null(ptr):
        return None
    raise TypeError('Unrecognized type.')

cdef python_to_unqlite_value(VM vm, unqlite_value *ptr, python_value):
    cdef unqlite_value *item_ptr = <unqlite_value *>0
    cdef bytes encoded_value

    if isinstance(python_value, unicode):
        encoded_value = encode(python_value)
        unqlite_value_string(ptr, encoded_value, -1)
    elif isinstance(python_value, bytes):
        unqlite_value_string(ptr, python_value, -1)
    elif isinstance(python_value, (list, tuple)):
        for item in python_value:
            item_ptr = vm.create_value(item)
            unqlite_array_add_elem(ptr, NULL, item_ptr)
            vm.release_value(item_ptr)
    elif isinstance(python_value, dict):
        for key, value in python_value.items():
            encoded_value = encode(key)
            item_ptr = vm.create_value(value)
            unqlite_array_add_strkey_elem(
                ptr,
                <const char *>encoded_value,
                item_ptr)
            vm.release_value(item_ptr)
    elif isinstance(python_value, bool):
        unqlite_value_bool(ptr, python_value)
    elif isinstance(python_value, (int, long)):
        unqlite_value_int64(ptr, python_value)
    elif isinstance(python_value, float):
        unqlite_value_double(ptr, python_value)
    else:
        unqlite_value_null(ptr)

cdef int unqlite_value_to_list(unqlite_value *key, unqlite_value *value, void *user_data):
    cdef list accum
    accum = <list>user_data
    accum.append(unqlite_value_to_python(value))

cdef int unqlite_value_to_dict(unqlite_value *key, unqlite_value *value, void *user_data):
    cdef dict accum
    accum = <dict>user_data
    pkey = unqlite_value_to_python(key)
    accum[pkey] = unqlite_value_to_python(value)
