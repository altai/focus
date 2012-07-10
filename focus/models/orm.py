# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


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
