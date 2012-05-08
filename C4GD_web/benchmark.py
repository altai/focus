# coding=utf-8
import time
from C4GD_web import app


class benchmark(object):
    def __init__(self, name, logger=app.logger.info):
        self.name = name
        self.logger = logger

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, ty, val, tb):
        self.logger('%s took %0.3f', self.name, time.time() - self.start)
        return False
