# coding=utf-8
import math
import flask


class Pagination(object):

    def __init__(self, total_count, page=False, per_page=False):
        self.page = page or int(flask.request.args.get('page', 1))
        self.per_page = per_page or per_page_value()
        if hasattr(total_count, '__len__'):
            self.total_count = len(total_count)
        else:
            self.total_count = total_count

    @property
    def pages(self):
        return int(math.ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
            yield num
            last = num

    def base(self):
        return (self.page - 1) * self.per_page

    def slice(self, data):
        return data[self.base():self.base() + self.per_page]

    def limit_offset(self):
        return (self.base(), self.per_page)


def per_page_value():
    return 20
