# coding=utf-8
import urllib, urlparse
from math import ceil
from flask import request, url_for
from C4GD_web import app


class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

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


from werkzeug.datastructures import iter_multi_items


def url_for_other_page(page):
    args = request.args.copy()
    args['page'] = page
    result = '%s?%s' % (
        request.path,
        urllib.urlencode(
            tuple(args.iterlists()), 
            doseq=1))
    return result
app.jinja_env.globals['url_for_other_page'] = url_for_other_page
