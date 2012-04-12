import functools

__all__ = ['plural']

def plural(method):
    method.is_plural = True
    return method

def method_decorator(http_method, path, is_plural=False, two_phase=False, silent=False):
    def wrapped(method):
        method.http_method = http_method
        method.is_plural = is_plural
        method.path = path
        method.two_phase = two_phase
        method.silent = silent
        return method
    return wrapped

def phases_decorator_factory(phase):
    def _decorator(method):
        assert hasattr(method, 'http_method'), 'Use method decorators (get, post, put, delete) before phase decorators (forth, back, both, blind).'
        method.phase = phase
        return method
    return _decorator

for method_name in ['get', 'post', 'put', 'delete']:       
    globals()[method_name] = functools.partial(method_decorator, method_name)
    __all__.append(method_name)
for phase, decorator_name in enumerate(['forth', 'back', 'both', 'blind'], 1):
    globals()[decorator_name] = phases_decorator_factory(phase)
    __all__.append(decorator_name)

