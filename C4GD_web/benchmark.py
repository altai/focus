# coding=utf-8
import time

from flask import current_app


class benchmark(object):
    def __init__(self, name, logger=None):
        self.name = name
        self.logger = logger or current_app.logger.info

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, ty, val, tb):
        self.logger('%s took %0.3f', self.name, time.time() - self.start)
        return False
