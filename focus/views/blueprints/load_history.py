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


"""Show load history to global admins.

CPU/Load Avg./Mem/free space/io-wait history of every compute node.
"""

import contextlib
import re
import urllib
import urlparse

import flask

from flask import blueprints
from focus.views import environments


bp = environments.admin(blueprints.Blueprint('load_history', __name__))


@bp.context_processor
def titles():
    return {
        'title': 'Load history',
        'subtitle': 'CPU/Load Avg./Mem/free space/io-wait history of every compute node'
        }

@bp.route('')
def index():
    '''Show html page with list of compute nodes.

    That page contains JS handling user's actions and showing graphics for
    every compute node/parameter/period requested.'''    
    return {'api': urlparse.urljoin(flask.request.url, 
                                    flask.url_for('.proxy', bypass='v0/'))}


@bp.route('proxy/<path:bypass>')
def proxy(bypass):
    '''Proxy requests to zabbix_proxy WSGI app for authorized.

    We already have authorization control (environments.admin).
    zabbix_proxy API provides GET endpoints only.
    '''
    if not re.match('^('
                    '|v0/'
                    '|v0/hosts/'
                    '|v0/periods/'
                    '|v0/parameters/'
                    '|v0/[^/]+/[^/]+/)$', 
                    bypass):
        flask.current_app.logger.info('Strange path requested: %s.' % bypass)
        flask.abort(404)
    baseurl = flask.current_app.config['ZABBIX_PROXY_BASEURL']
    if not baseurl.endswith('/'):
        baseurl += '/'
    url = urlparse.urljoin(baseurl, bypass)
    if len(flask.request.args):
        url = '%s?%s' % (url, urllib.urlencode(flask.request.args))
    flask.current_app.logger.debug('Going to proxy to zabbix proxy "%s"' % url)
    with contextlib.closing(urllib.urlopen(url)) as fp:
        content = fp.read()
        url_root = flask.request.url.split('proxy/%s' % bypass)[0] + 'proxy/'
        screened = content.replace(baseurl, url_root)
        flask.current_app.logger.debug(
            'Response from zabbix proxy "%s", screened "%s"' % (content, screened))
        return flask.make_response(screened)
