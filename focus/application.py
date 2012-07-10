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


import sys

import flask
import werkzeug


class FatFlask(flask.Flask):
    jinja_options = werkzeug.ImmutableDict(
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
            'hamlish_jinja.HamlishExtension']
    )

    def make_response(self, rv):
        if type(rv) is dict:
            template_name = "/".join(flask.request.endpoint.split('.'))
            result = flask.render_template(
                template_name + self.config['TEMPLATE_EXTENSION'], **rv)
        elif type(rv) in (list, tuple) and len(rv) == 2:
            result = flask.render_template(rv[0], **rv[1])
        else:
            result = rv
        return super(FatFlask, self).make_response(result)

    def full_dispatch_request(self):
        if self.debug:
            return super(FatFlask, self).full_dispatch_request()
        else:
            try:
                return super(FatFlask, self).full_dispatch_request()
            except Exception, error:
                flask.flash(error.message, 'error')
                exc_type, exc_value, tb = sys.exc_info()
                self.log_exception((exc_type, exc_value, tb))
                return flask.render_template('blank.haml')
