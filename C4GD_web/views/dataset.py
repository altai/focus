class Column(object):
    sorted = None
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
    mapping = {}
    default_names = []
    selected = []
    spare = []
    ordering = []
    current_names = []
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
        self.current_names = names

    def order(self, asc=[], desc=[]):
        self.ordering = []
        for name in self.current_names:
            if name in asc:
                self.ordering.append((name, 'asc'))
                self.selected[self.index(name)].sorted = 'asc'
            if name in desc:
                self.ordering.append((name, 'desc'))
                self.selected[self.index(name)].sorted = 'desc'
                
    def index(self, attr_name):
        return self.current_names.index(attr_name)


    

class DataSet(object):
    data = []
    columns = None

    def __init__(self, objects, columns):
        self.columns = columns
        self.data = [[x(obj) for x in self.columns.selected] for obj in objects]
        if self.columns.ordering:
            ordering = dict(self.columns.ordering)
            def _cmp(x, y):
                for attr_name in self.columns.current_names:
                    if attr_name in ordering:
                        xs = lambda i: i[self.columns.index(attr_name)]
                        if ordering[attr_name] == 'asc':
                            r = cmp(xs(x), xs(y))
                        else:
                            r = cmp(xs(y), xs(x))
                        if r:
                            return r
                return 0
            self.data = sorted(self.data, cmp=_cmp)

