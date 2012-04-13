class Column(object):
    def __init__(self, attr_name, verbose_name=None):
        self.attr_name = attr_name
        self.verbose_name = verbose_name or attr_name

    def __call__(self, obj):
        return self.adapt(getattr(obj, self.attr_name))

    def adapt(self, value):
        raise NotImplementedError

class IntColumn(Column):
    adapt = int

class StrColumn(Column):
    adapt = str


class ColumnKeeper(object):
    is_changed = False
    def __init__(self, mapping, default_names=[]):
        self.mapping = mapping
        self.default_names = default_names
        self.adjust(default_names)

    def adjust(self, names):
        from C4GD_web.utils import select_keys
        self.selected = list(select_keys(self.mapping, names, True))
        self.spare = list(select_keys(
                self.mapping, set(self.mapping) - set(names)))
        if names != self.default_names:
            self.is_changed = True
