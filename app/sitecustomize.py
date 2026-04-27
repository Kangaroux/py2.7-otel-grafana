"""sitecustomize.py - Patches for Python 2.7 runtime compatibility.

This file runs automatically at Python startup (before any user code),
making backported stdlib features available under their standard names.
"""
import functools
import time
import types
import threading

# --------------------------------------------------------------------------
# functools.lru_cache  (added Python 3.2)
# --------------------------------------------------------------------------
if not hasattr(functools, 'lru_cache'):
    from backports.functools_lru_cache import lru_cache
    functools.lru_cache = lru_cache

# --------------------------------------------------------------------------
# time.time_ns  (added Python 3.7)
# --------------------------------------------------------------------------
if not hasattr(time, 'time_ns'):
    def _time_ns():
        return int(time.time() * 1e9)
    time.time_ns = _time_ns

# --------------------------------------------------------------------------
# types.MappingProxyType  (added Python 3.3)
# --------------------------------------------------------------------------
if not hasattr(types, 'MappingProxyType'):
    class _MappingProxyType(object):
        """Read-only dict view, minimal backport for Python 2.7."""
        __slots__ = ('_data',)

        def __init__(self, data):
            object.__setattr__(self, '_data', dict(data))

        def __getitem__(self, key):
            return self._data[key]

        def __contains__(self, key):
            return key in self._data

        def __iter__(self):
            return iter(self._data)

        def __len__(self):
            return len(self._data)

        def __repr__(self):
            return 'mappingproxy({0!r})'.format(self._data)

        def get(self, key, default=None):
            return self._data.get(key, default)

        def keys(self):
            return self._data.keys()

        def values(self):
            return self._data.values()

        def items(self):
            return self._data.items()

        def copy(self):
            return self._data.copy()

    types.MappingProxyType = _MappingProxyType

# --------------------------------------------------------------------------
# threading.get_ident  (added Python 3.3, was thread.get_ident in 2.7)
# --------------------------------------------------------------------------
if not hasattr(threading, 'get_ident'):
    import thread
    threading.get_ident = thread.get_ident

# --------------------------------------------------------------------------
# threading.Thread(daemon=...) keyword argument  (added Python 3.3)
# In Python 2.7 you must set thread.daemon = True after construction.
# Wrap __init__ rather than subclassing to avoid breaking _DummyThread.
# --------------------------------------------------------------------------
_orig_thread_init = threading.Thread.__init__
def _patched_thread_init(self, *args, **kwargs):
    daemon = kwargs.pop('daemon', None)
    _orig_thread_init(self, *args, **kwargs)
    if daemon is not None:
        self.daemon = daemon
threading.Thread.__init__ = _patched_thread_init

# --------------------------------------------------------------------------
# dataclasses module  (added Python 3.7)
# The otel python27 branch removed @dataclass decorators but left the
# imports. Provide a stub module so 'from dataclasses import dataclass' works.
# --------------------------------------------------------------------------
import sys
if 'dataclasses' not in sys.modules:
    _dc_mod = types.ModuleType('dataclasses')
    def _dataclass(cls=None, **kwargs):
        if cls is None:
            return lambda c: c
        return cls
    _dc_mod.dataclass = _dataclass
    _dc_mod.field = lambda **kw: None
    _dc_mod.fields = lambda obj: []
    sys.modules['dataclasses'] = _dc_mod

# --------------------------------------------------------------------------
# urllib.parse  (Python 3 reorganisation of urlparse + urllib)
# --------------------------------------------------------------------------
if 'urllib.parse' not in sys.modules:
    import urlparse as _urlparse
    import urllib as _urllib
    _parse_mod = types.ModuleType('urllib.parse')
    # Copy everything from urlparse (urlparse, urlunparse, urljoin, etc.)
    for _name in dir(_urlparse):
        if not _name.startswith('_'):
            setattr(_parse_mod, _name, getattr(_urlparse, _name))
    # Add urllib functions (quote, urlencode, etc.)
    for _name in ('quote', 'quote_plus', 'unquote', 'unquote_plus',
                   'urlencode', 'pathname2url', 'url2pathname'):
        if hasattr(_urllib, _name):
            setattr(_parse_mod, _name, getattr(_urllib, _name))
    sys.modules['urllib.parse'] = _parse_mod
    # Also set as attribute so 'from urllib import parse' works
    import urllib
    urllib.parse = _parse_mod
