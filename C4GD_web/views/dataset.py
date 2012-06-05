# coding=utf-8
import copy

from C4GD_web.clients import clients
from C4GD_web.utils import select_keys


class Column(object):
    sorted = None
    def __init__(self, attr_name, verbose_name=None):
        self.attr_name = attr_name
        self.verbose_name = verbose_name or attr_name

    def __call__(self, obj):
        return self.adapt(obj[self.attr_name])

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
    groupby = []

    def __init__(self, mapping, default_names=[]):
        self.mapping = mapping
        self.default_names = default_names
        self.adjust(default_names)

    def adjust(self, names):
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


    def adjust_groupby(self, code):
        attr_name, value = code.split('|')
        if attr_name in self.current_names:
            self.groupby = attr_name, value
    

class DataSet(object):
    data = []
    columns = None

    def __init__(self, objects, columns):
        self.columns = columns
        # load data
        self.flat_data = [[x(obj) for x in self.columns.selected] for obj in objects]
        # group it
        if self.columns.groupby:
            attr_name, value = self.columns.groupby
            self.data = []
            self.data.append({'description': 'Cloud statistics'})
            distinct_values = self.get_distinct_values(attr_name)
            if value and value in distinct_values:
                self.data.extend(self.get_group_for(attr_name, value))
            else:
                for x in distinct_values:
                    self.data.extend(self.get_group_for(attr_name, x))
        else:
            self.data = copy.deepcopy(self.flat_data)
        # sort it with respect to grouping
        if self.columns.ordering and len(self.flat_data):
            if self.columns.groupby:
                # grouping required
                attr_name, value = self.columns.groupby
                if value:
                    # filter out only rows for this value of grouper attr
                    def group_rows_filter(x):
                        # data row or header row
                        return type(x) is list and x[self.columns.index(attr_name)] == value \
                            or x['value'] == value
                    data = filter(group_rows_filter, self.data[1:])
                    # preserve cloud statistics at index 0
                    self.data[1:] = data
                    # preserve group statistics at index 1
                    self.data[2:] = self.order_dataset(self.data[2:]) # leave group stat
                else:
                    # separate rows of data into buckets based on grouping value
                    # order each group
                    # glue up groups respecting ordering by attr_name if exists

                    # separate
                    last_group = self.data[1]['value']# it exists because flat data exist
                    hashed_data = {last_group: [self.data[1]]}
                    for row in self.data[2:]:
                        if type(row) is list and row[self.columns.index(attr_name)] == last_group:
                            hashed_data[last_group].append(row)
                        else:
                            if 'value' in row:
                                last_group = row['value']
                                hashed_data[last_group] = [row]
                    # order
                    for k, v in hashed_data.items():
                        # preserve group statistics header
                        hashed_data[k][1:] = self.order_dataset(v[1:])
                    # glue up
                    values = hashed_data.keys()
                    ordering = dict(self.columns.ordering)
                    if attr_name in ordering:
                        values = sorted(values, reverse=ordering[attr_name] == 'desc')
                    self.data = self.data[:1]
                    for x in values:
                        self.data.extend(hashed_data[x])
            else:
                self.data = self.order_dataset(self.data)

    def order_dataset(self, data):
        data = copy.deepcopy(data)
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
        result = sorted(data, cmp=_cmp)
        return result
        
    def get_distinct_values(self, attr_name):
        return list(set([x[self.columns.index(attr_name)] for x in self.flat_data]))

    def get_group_for(self, attr_name, value):
        index = self.columns.index(attr_name)
        result = [{'description': 'Group statistics for %s=%s' % (attr_name, value), 'value': value}] + [x for x in self.flat_data if x[index] == value]
        return result

        
            
