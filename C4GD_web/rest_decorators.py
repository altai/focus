import functools

__all__ = []

def method_decorator(http_method, path, is_plural=False, two_phase=False):
    def wrapped(method):
        method.http_method = http_method
        method.is_plural = is_plural
        method.path = path
        method.two_phase = two_phase
        return method
    return wrapped


for method_name in ['get', 'post']:       
    globals()[method_name] = functools.partial(method_decorator, method_name)
    __all__.append(method_name)
