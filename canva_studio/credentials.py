"""Encrypt portable credential files for the current Windows user."""
import base64
import ctypes as ct
import json
import os
from ctypes import wintypes as wt

from .core import atomic_json


class Blob(ct.Structure):
    _fields_ = [('size', wt.DWORD), ('data', ct.c_void_p)]


def protect(data, decrypt=False):
    if os.name != 'nt':
        raise OSError('Windows mới hỗ trợ lưu khóa mã hóa trong SKST.')
    crypt = ct.WinDLL('crypt32', use_last_error=True)
    fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes = [ct.POINTER(Blob), ct.c_void_p, ct.c_void_p, ct.c_void_p,
                   ct.c_void_p, wt.DWORD, ct.POINTER(Blob)]
    fn.restype = wt.BOOL
    buffer = ct.create_string_buffer(data)
    source, result = Blob(len(data), ct.addressof(buffer)), Blob()
    if not fn(ct.byref(source), None, None, None, None, 1, ct.byref(result)):
        raise OSError(ct.get_last_error(), 'Windows chưa đọc hoặc ghi được thông tin đăng nhập đã mã hóa.')
    free = ct.WinDLL('kernel32').LocalFree
    free.argtypes = [ct.c_void_p]
    free.restype = ct.c_void_p
    try:
        return ct.string_at(result.data, result.size)
    finally:
        free(result.data)


def load(path):
    try:
        encoded = json.loads(path.read_text(encoding='utf8'))['protected']
        result = json.loads(protect(base64.b64decode(encoded, validate=True), decrypt=True))
        if not isinstance(result, dict):
            raise ValueError
        return result
    except FileNotFoundError:
        return {}
    except (KeyError, TypeError, ValueError) as exc:
        raise OSError('Tệp thông tin đăng nhập không đọc được.') from exc


def save(path, value):
    if not value:
        path.unlink(missing_ok=True)
        return
    encrypted = protect(json.dumps(value, ensure_ascii=False).encode('utf8'))
    atomic_json(path, {'protected': base64.b64encode(encrypted).decode('ascii')})
