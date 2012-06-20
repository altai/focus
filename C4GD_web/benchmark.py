# coding=utf-8
import time

import flask


class T(object):
    def __init__(self, name, logger=None):
        self.name = name
        self.logger = logger or flask.current_app.logger.info

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, ty, val, tb):
        self.logger('%s took %0.3f', self.name, time.time() - self.start)
        return False
