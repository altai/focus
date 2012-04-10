import functools

__all__ = []

def method_decorator(http_method, path, is_plural=False, two_phase=False, silent=False):
    def wrapped(method):
        method.http_method = http_method
        method.is_plural = is_plural
        method.path = path
        method.two_phase = two_phase
        method.silent = silent
        return method
    return wrapped


for method_name in ['get', 'post', 'put', 'delete']:       
    globals()[method_name] = functools.partial(method_decorator, method_name)
    __all__.append(method_name)
