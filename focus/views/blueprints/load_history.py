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
import datetime
import json
import re
import urllib
import urlparse

import flask

from flask import blueprints
from focus.models import orm
from focus.views import environments


bp = environments.admin(blueprints.Blueprint('load_history', __name__))


def baseurl():
    url = flask.current_app.config['ZABBIX_PROXY_BASEURL']
    if not url.endswith('/'):
        url += '/'
    return url


@bp.context_processor
def titles():
    return {
        'title': 'Load history',
        'subtitle': 'CPU/Load Avg./Mem/free space/io-wait history of every compute node'
        }

COMPUTE_ON = 0
COMPUTE_OFF = 1
COMPUTE_NOT_RESPONDING = 2


def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


def compute_statuses((host, updated_at, created_at, disabled)):
    AVAILABLE_DUE = 60 # seconds compute service is alive since last check
    # NOTE(apugachev) we'd survive doing it in this cycle
    NOW = datetime.datetime.now()
    if disabled:
        status = COMPUTE_OFF
    elif total_seconds(((updated_at or created_at) - NOW) > AVAILABLE_DUE:
        status = COMPUTE_NOT_RESPONDING
    else:
        status = COMPUTE_ON
    return host, status


def get_compute_nodes_with_statuses():
    """Return list of compute nodes with statuses.

    (('n005', 1), ('n007', 0), ('n008', 2))
    """
    db = orm.get_store('NOVA_RO')
    data = db.execute("SELECT host, updated_at, created_at, disabled FROM services WHERE deleted = 0 AND topic LIKE 'compute'").get_all()
    NOW = datetime.datetime.now()
    return map(compute_statuses, data)


def get_api_data(path):
    content = _proxy(path)
    return json.loads(content)


@bp.route('')
def index():
    """Show html page with list of compute nodes.

    That page contains JS handling user's actions and showing graphics for
    every compute node/parameter/period requested."""
    # TODO(apugachev) retrieve nodes from /os-nodes when have openstack env
    compute_data = dict(get_compute_nodes_with_statuses())
    zabbix_data = dict(get_api_data('v0/hosts_statuses/')['hosts_statuses'])
    data = []
    ZABBIX_OFF = 1
    for host in sorted(set(compute_data.keys()).union(set(zabbix_data.keys()))):
        data.append((
            host, 
            compute_data.get(host, COMPUTE_OFF), 
            zabbix_data.get(host, ZABBIX_OFF),
            zabbix_data.has_key(host)))
    return {'data': data}


@bp.route('show/<host>/')
def show(host):
    """Show html page with graphics for selected host."""
    periods = get_api_data('v0/periods')['periods']
    template = 'v0/%(host)s/%(period)s/?parameters=%(parameters)s&width=780&height=240'
    data = {}
    parameters = {
        'cpu_url': 'avg1,avg5,avg15,iowait&title=CPU%20Usage',
        'memory_url': 'freemem,usedmem&title=Memory%20Usage',
        'disk_url': 'freespace&title=Disk%20Usage',
        'swap_url': 'freeswap&title=Swap%20Usage'}
    for x in periods:
        data[x] = {}
        for k, v in parameters.items():
            d = {'period': x, 'host': host, 'parameters': v}
            data[x][k] = _screen(urlparse.urljoin(baseurl(), template % d))
    return {'subtitle':  'Graphics for host %s' % host,
            'data': data, 'periods': periods, 'host': host}


def _screen(text):
    url_root = urlparse.urljoin(flask.request.url_root, '/global/load_history/proxy/')
    return text.replace(baseurl(), url_root)
    
    
def _proxy(bypass, content_type=None):
    url = urlparse.urljoin(baseurl(), bypass)
    if len(flask.request.args):
        url = '%s?%s' % (url, urllib.urlencode(flask.request.args))
    if flask.current_app.debug:
        flask.current_app.logger.debug(
            'Going to proxy to zabbix proxy "%s"' % url)
    with contextlib.closing(urllib.urlopen(url)) as fp:
        content = fp.read()
        content_type = fp.info().getheader('Content-Type')
        if 'json' in content_type:
            screened = _screen(content)
            if flask.current_app.debug:
                flask.current_app.logger.debug(
                    'Response from zabbix proxy "%s", screened "%s"' % (
                        content, screened))
            return screened
        else:
            return content


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
                    '|v0/hosts_statuses/'
                    '|v0/[^/]+/[^/]+/)$', 
                    bypass):
        flask.current_app.logger.info('Strange path requested: %s.' % bypass)
        flask.abort(404)
    content_type = None
    response = flask.make_response(_proxy(bypass, content_type))
    response.headers['Content-Type'] = content_type
    return response
