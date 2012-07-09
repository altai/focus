# coding=utf-8
# TODO(apugachev) make decorator to use with views like
# @with_db('RO')
# def index(...):
#     g.db.(...
# @with_db('RO', 'foo')
# def index():
#     g.foo.execute(...
# and make context manager to use in other places like
# with in_storm('RO') as db:
#     db.execute(...
# Commits should be done by user, connection closed by object.
import flask
from storm import locals


def get_store(SETTINGS_PREFIX):
    return locals.Store(locals.create_database(
        flask.current_app.config[SETTINGS_PREFIX + '_DATABASE_URI']))
