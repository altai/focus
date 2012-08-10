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

import fcntl
import logging
import os
import os.path
import re
import socket
import thread
import time
import urlparse

import eventlet
import flask
import rrdtool
import MySQLdb


app = flask.Flask(__name__)

app.config.from_object('focus.zabbix_proxy.default_settings')

try:
    app.config.from_object('focus.local_settings')
except ImportError:
    pass
try:
    app.config.from_pyfile("/etc/focus/local_settings.py")
except IOError:
    pass


CONSUMER_LOG = logging.getLogger("zabbix_proxy_api.consumer")


class RRDKeeper(object):
    # smallest common divider of item delays was choosen as step interval for DB
    # this number must give integer number for spans (see SPAN_6H)
    STEP_INTERVAL = 30

    # heartbeat parameter must be twice as big as delay of an item
    # delays of items were taken from "items" table of Zabbix db
    DATASOURCES = [
        'DS:avg1:GAUGE:120:U:U',
        'DS:avg5:GAUGE:600:U:U',
        'DS:avg15:GAUGE:1800:U:U',
        'DS:freemem:GAUGE:60:U:U',
        'DS:usedmem:GAUGE:60:U:U',
        'DS:freeswap:GAUGE:60:U:U',
        'DS:freespace:GAUGE:60:U:U',
        'DS:iowait:GAUGE:120:U:U'
        ]

    # man rrdtool
    # steps is number of PDPs to pass to CF to get 1 point of RRA
    # if PDP frequency is 2 seconds then steps for 100 points in 6 hours
    # interval is 6 * 60 * 60 / 100 / 2 = 108
    POINTS_PER_GRAPH = 10
    SPAN_6H = 6 * 60 * 60 / POINTS_PER_GRAPH / STEP_INTERVAL
    # 100 points for 1 day
    SPAN_1D = SPAN_6H * 4
    # 100 points for 1 week
    SPAN_1W = SPAN_1D * 7
    # 100 points for 1 month
    SPAN_1M = SPAN_1D * 30
    # 100 points for 1 year
    SPAN_1Y = SPAN_1D * 365

    DESCRIPTIONS_TO_DATASOURCE_NAMES = {
        'CPU Load Average 1': 'avg1',
        'CPU Load Average 5': 'avg5',
        'CPU Load Average 15': 'avg15',
        'Free memory(%)': 'freemem',
        'Used memory(%)': 'usedmem',
        'Available Swap(%)': 'freeswap',
        'Free disk space on $1': 'freespace',
        'CPU iowait': 'iowait'
        }
    def __init__(self, path):
        self.path = os.path.abspath(path)
        
    @staticmethod
    def _fname(path, host):
        return os.path.join(path, 
                            '%s.rrd' % re.sub('[^a-zA-Z0-9_.-]', '', host))
    
    def fname(self, host):
        return self._fname(self.path, host)

    def ensure_rrd_existence(self, hosts):
        """Create RRD files for each host."""
        for h in hosts:
            db_filename = self.fname(h)
            if not os.path.isfile(db_filename):
                start = '01/01/80'
                rras = [
                    'RRA:AVERAGE:0.99999:%s:%s' % (
                        self.SPAN_6H, self.POINTS_PER_GRAPH),
                    'RRA:AVERAGE:0.99999:%s:%s' % (
                        self.SPAN_1D, self.POINTS_PER_GRAPH),
                    'RRA:AVERAGE:0.99999:%s:%s' % (
                        self.SPAN_1W, self.POINTS_PER_GRAPH),
                    'RRA:AVERAGE:0.99999:%s:%s' % (
                        self.SPAN_1M, self.POINTS_PER_GRAPH),
                    'RRA:AVERAGE:0.99999:%s:%s' % (
                        self.SPAN_1Y,  self.POINTS_PER_GRAPH)
                    ]
                CONSUMER_LOG.info(
                    'Creating RRD  %s\nStart: %s\nStep: %s\n'
                    'Datasources: %s\nRRAs: %s' % (
                        db_filename, start, 
                        str(self.STEP_INTERVAL), self.DATASOURCES, rras))
                rrdtool.create(
                    db_filename,
                    '--start', start,
                    '--step', str(self.STEP_INTERVAL),
                    self.DATASOURCES,
                    *rras)

    def update(self, data, items_2_hosts, items_2_descriptions):
        """Update RRD files with the data.

        To minimize rrdtool.update callse we need to rearrange the data:
        
        update filename [--template|-t ds-name[:ds-name]...] \
        N|timestamp:value[:value...] [timestamp:value[:value...] ...]
        """
        host_data = {}
        host_datasources = {}
        for itemid, clock, value in data:
            host = items_2_hosts[itemid]
            if host not in host_data:
                host_data[host] = {}
            description = items_2_descriptions[itemid]
            try:
                ds = self.DESCRIPTIONS_TO_DATASOURCE_NAMES[description]
            except KeyError, e:
                pass
            else:
                if clock not in host_data[host]:
                    host_data[host][clock] = {}
                host_data[host][clock][ds] = value
                if host not in host_datasources:
                    host_datasources[host] = []
                if ds not in host_datasources[host]:
                    host_datasources[host].append(ds)
        for host, samples in host_data.items():
            datasources = ':'.join(host_datasources[host])
            values = []
            for clock, dots in sorted(samples.items(), key=lambda x: x[0]):
                row = [str(clock)]
                for ds in host_datasources[host]:
                    row.append(str(dots.get(ds, 'U')))
                values.append(':'.join(row))
            CONSUMER_LOG.debug(values)
            CONSUMER_LOG.debug(datasources)
            rrdtool.update(self.fname(host), 
                           '-t', datasources,
                           *values)


class LastSecond(object):
    _second = 0

    def __init__(self, path, table):
        self.fname = os.path.join(path, '%s.last_second' % table)
    
    def get_second(self):
        try:
            with open(self.fname, 'r') as f:
                self._second = int(f.read())
        except IOError, e:
            pass
        return self._second

    def set_second(self, second):
        self._second = second

    def commit(self):
        try:
            with open(self.fname, 'w') as f:
                f.write(str(self._second))
        except OSError, e:
            CUSTOMER_LOG.exception(
                'Can\'t open last second file %s: %s' % (
                    self.fname, str(e)))

    second = property(get_second, set_second)


class ZabbixConsumer(object):
    c = None    

    def __init__(self, c, path):
        self.c, self.path = c, path

    def get_data(self):
        # for each table history, history_uint
        #   get last second
        #   get everything after the last second
        #   update last known second
        data = []
        second_savers = []
        for t in ('history', 'history_uint'):
            x = LastSecond(self.path, t)
            #FIXME - check clock field has index in db
            self.c.execute(
                'SELECT itemid, clock, value FROM %s WHERE clock > %%s ORDER BY clock' % t, 
                (x.second,))
            tmp = self.c.fetchall()
            data.extend(tmp)
            if len(tmp):
                x.second = data[-1][1]
            second_savers.append(x)
        return data, second_savers

    def get_hosts(self):
        # Sozinov says templates have status 3
        self.c.execute('SELECT host FROM hosts WHERE status <> 3')
        hosts = [x[0] for x in self.c.fetchall()]
        items_2_hosts = {}
        items_2_descriptions = {}
        self.c.execute('SELECT itemid, host, description FROM items JOIN hosts ON (items.hostid = hosts.hostid)')
        for itemid, host, description in self.c.fetchall():
            items_2_hosts[itemid] = host
            items_2_descriptions[itemid] = description
        return hosts, items_2_hosts, items_2_descriptions


class Locker(type):
    lock = thread.allocate_lock()

    def __new__(cls, name, bases, dct):
        obj = type.__new__(cls, name, bases, dct)
        obj.lock = cls.lock
        return obj


class ZabbixRRDFeeder(object):
    db = None
    def __init__(self):
        self.path = os.path.abspath(app.config['ZABBIX_PROXY_TMP'])
        self.db_config = app.config['ZABBIX_PROXY_DB']
        thread.start_new_thread(self.consume, ())
        #self.consume()
        CONSUMER_LOG.info('Consumer started.')


    def reconnect(self):
        if self.db is not None:
            try:
                self.db.close()
            except self.db.connection_errors:
                pass
            time.sleep(1)
        try:
            self.db = MySQLdb.connect(**self.db_config)
        except Exception, e:
            CONSUMER_LOG.exception('Failed to connect to Zabbix db: %s', str(e))

    def consume(self):
        with open(os.path.join(self.path, 'consume.lock'), 'w') as fd:
            fcntl.lockf(fd, fcntl.LOCK_EX)        
            with Locker('Locker', (), {})().lock:
                CONSUMER_LOG.info('Consuming now in %s.' % os.getpid())
                while True:
                    self.reconnect()
                    try:
                        cursor = self.db.cursor()
                    except Exception, e:
                        CONSUMER_LOG.exception(
                            'Failed to get cursor for Zabbix db: %s', 
                            str(e))
                    else:
                        try:
                            z = ZabbixConsumer(cursor, self.path)
                            r = RRDKeeper(self.path)
                            # get hosts and items
                            hosts, items_2_hosts, items_2_descriptions = z.get_hosts()
                            # init missing RRD files
                            r.ensure_rrd_existence(hosts)
                            # get historic data 
                            data, second_savers = z.get_data()
                            # save data in rrd
                            r.update(data, items_2_hosts, items_2_descriptions)
                            # commit last known seconds after rrdtool saved new data
                            [x.commit() for x in second_savers]

                        except Exception, e:
                            CONSUMER_LOG.exception(
                                'Error during consumerism: %s', 
                                str(e))
            fcntl.lockf(fd, fcntl.LOCK_UN)
        CONSUMER_LOG.info('Unlocked everything.')


ZabbixRRDFeeder()


def url(*args, **kwargs):
    return urlparse.urljoin(flask.request.url_root, 
                            flask.url_for(*args, **kwargs))

@app.route('/')
def versions():
    return flask.json.dumps({
        'versions': [url('discover', version='0')]
        })


PERIODS = ['6h', '1d', '1w', '1m', '1y']
PARAMETERS = [
    'avg1', 
    'avg5',
    'avg15', 
    'freemem', 
    'usedmem',
    'freeswap',
    'freespace',
    'iowait'
]

@app.route('/v<version>/')
def discover(version):
    if version == '0':
        return flask.json.dumps({
            'version': version,
            'endpoints': {
                'hosts': url('hosts', version=version),
                'periods': url('periods', version=version),
                'parameters': url('parameters', version=version),
                'data': '%s?parameters=param1,param2' % url('data', 
                            version=version, 
                            host='_host_',
                            period='_period_')
                }
            })
    flask.abort(404)


@app.route('/v<version>/hosts/')
def hosts(version):
    # TODO: use IPs as names for rrd files, list dir and return here
    if version == '0':
        return flask.json.dumps([
                x.replace('.rrd', '') for x in os.listdir(
                    os.path.abspath(
                        flask.current_app.config['ZABBIX_PROXY_TMP'])
                    ) if x.endswith('.rrd')])
    flask.abort(404)


@app.route('/v<version>/periods/') 
def periods(version):
    if version == '0':
        return flask.json.dumps(PERIODS)
    flask.abort(404)


@app.route('/v<version>/parameters/')
def parameters(version):
    if version == '0':
        return flask.json.dumps(PARAMETERS)
    flask.abort(404)


@app.route('/v<version>/<host>/<period>/')
def data(version, host, period):
    if version == '0':
        parameters = flask.request.args.get('parameters', None)
        if parameters is not None:
            parameters = parameters.split(',')
            for i in parameters:
                if i not in PARAMETERS:
                    flask.abort(404)
        else:
            parameters = PARAMETERS
        if period not in PERIODS:
            flask.abort(404)
        RESOLUTIONS = {
            '6h': 6 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH,
            '1d': 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH,
            '1w': 7 * 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH,
            '1m': 30 * 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH, 
            '1y': 365 * 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH
            }
        fname = RRDKeeper._fname(os.path.abspath(
                flask.current_app.config['ZABBIX_PROXY_TMP']), host)
        if not os.path.isfile(fname):
            flask.abort(404)
        args = map(str,
                   [fname,
                    'AVERAGE',
                    '-r', '%s' % str(RESOLUTIONS[period]),
                    '-s', 'end-%s' % period,
                    '-e', 'now'])
        data = rrdtool.fetch(*args)
        indexes = [data[1].index(x) for x in parameters]
        result = [data[0], 
                  [data[1][i] for i in indexes], 
                  [[[row[i] for i in indexes] for row in data[2]]]]
        return flask.json.dumps(result)
    flask.abort(404)
