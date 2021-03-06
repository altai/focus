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

"""Pumps data from Zabbix DB and provides it with HTTP API.

Hosts with status 0 are real hosts, not templates.
Items store histori data in few tables depending on values type:
+------------------+--------------+
| items.value_type |  table name  |
+------------------+--------------+
|        0         |   history    |
|        3         | history_uint |
+------------------+--------------+

Data is collected by Zabbix with different time delay. This makes signals
with bigger delay have more error when stored in a single RRD file. To
avoid this we store every item data for every host in a separate RRD file.
rrdtool graph then consolidates data to build graphics.

"""

import datetime
import fcntl
import logging
import os
import os.path
import re
import socket
import tempfile
import thread
import time
import urlparse

import flask
import rrdtool
import MySQLdb
import _mysql


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
KEYS_TO_DATASOURCE_NAMES = {
    'system.cpu.load[,avg1]': 'avg1',       # CPU Load Average 1
    'system.cpu.load[,avg5]': 'avg5',       # CPU Load Average 5
    'system.cpu.load[,avg15]': 'avg15',     # CPU Load Average 15
    'vm.memory.size[pfree]': 'freemem',     # Free memory(%)
    'vm.memory.size[pused]': 'usedmem',     # Used memory(%)
    'system.swap.size[,pfree]': 'freeswap', #Available Swap(%)
    'vfs.fs.size[/,free]': 'freespace',     #Free disk space on $1
    'system.cpu.util[,iowait]': 'iowait'    #CPU iowait'
}
ITEMS_KEYS = ','.join(
    map(lambda x: "'%s'" % _mysql.escape_string(x),
        KEYS_TO_DATASOURCE_NAMES.keys()))
ITEM_VALUE_TYPE_2_TABLE_NAME = {0: 'history', 3: 'history_uint'}
COLORS = [
    '000080',
    '008000',
    '800000',
    '0000FF',
    '00FF00',
    'FF0000',
    '800080',
    '008080',
    '808000'
    ]
    
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

API_LOG = logging.getLogger("zabbix_proxy_api.service")
CONSUMER_LOG = logging.getLogger("zabbix_proxy_api.consumer")
API_LOG.propagate = False
CONSUMER_LOG.propagate = False
API_LOG.setLevel(logging.DEBUG if app.debug else logging.WARNING)
CONSUMER_LOG.setLevel(logging.DEBUG if app.debug else logging.WARNING)
if app.config.get('ZABBIX_LOG_FILE', '') != '':
    rotating_file_handler = logging.handlers.RotatingFileHandler(
        app.config['ZABBIX_LOG_FILE'],
        maxBytes=app.config['ZABBIX_LOG_MAX_BYTES'],
        backupCount=app.config['ZABBIX_LOG_BACKUP_COUNT'])
    rotating_file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
            ))
    API_LOG.addHandler(rotating_file_handler)
    CONSUMER_LOG.addHandler(rotating_file_handler)

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
    POINTS_PER_GRAPH = 100
    

    def __init__(self, path):
        self.path = os.path.abspath(path)
        
    @staticmethod
    def fname(path, host, ds_name):
        name = '%s.%s.rrd' % (str(host), ds_name)
        return os.path.join(path, name)

    def ensure_rrd_existence(self, host, ds_name, step):
        """Create RRD files for the host/item combination."""
        db_filename = self.fname(self.path, host, ds_name)
        if not os.path.isfile(db_filename):
            # it is better to take little bit more points then exact value
            # because dividing by 100 can eat some and because interpolation
            # is better on bigger datasets (it will occur when RRD will build 
            # a graph later)
            SPAN_6H = 8 * 60 * 60 / self.POINTS_PER_GRAPH / step or 1
            SPAN_1D = 5 * 6 * 60 * 60 / self.POINTS_PER_GRAPH / step or 1
            SPAN_1W = 10 * 24 * 60 * 60 / self.POINTS_PER_GRAPH / step or 1
            SPAN_1M = 40 * 24 * 60 * 60 / self.POINTS_PER_GRAPH / step or 1
            SPAN_1Y = 380 * 24 * 60 * 60 / self.POINTS_PER_GRAPH / step or 1
            rras = [
                'RRA:AVERAGE:0.5:1:%s' % self.POINTS_PER_GRAPH,
                'RRA:AVERAGE:0.99999:%s:%s' % (
                    SPAN_6H, self.POINTS_PER_GRAPH),
                'RRA:AVERAGE:0.99999:%s:%s' % (
                    SPAN_1D, self.POINTS_PER_GRAPH),
                'RRA:AVERAGE:0.99999:%s:%s' % (
                    SPAN_1W, self.POINTS_PER_GRAPH),
                'RRA:AVERAGE:0.99999:%s:%s' % (
                    SPAN_1M, self.POINTS_PER_GRAPH),
                'RRA:AVERAGE:0.99999:%s:%s' % (
                    SPAN_1Y,  self.POINTS_PER_GRAPH)
                ]
            # workaround, otherwise rrdtool.create file with empty points
            # starting at current moment and it is impossible to add old data
            START = '01/01/80'
            
            args = (db_filename,
                '--start', str(START),
                '--step', str(step),
                'DS:%s:GAUGE:%s:U:U' % (ds_name, str(step * 2)))
            rrdtool.create(
                db_filename,
                '--start', str(START),
                '--step', str(step),
                'DS:%s:GAUGE:%s:U:U' % (ds_name, str(step * 2)),
                *rras)

    def update(self, data, items_2_hosts, items_2_keys, items_2_delays):
        """Update RRD files with the data.
        
        Ensure file exists.
        """
        for itemid, samples in data.items():
            if len(samples):
                hostid = items_2_hosts[itemid]
                key_ = items_2_keys[itemid]
                ds_name = KEYS_TO_DATASOURCE_NAMES[key_]
                self.ensure_rrd_existence(hostid, ds_name, items_2_delays[itemid])
                values = ['%s:%s' % x for x in samples]
                rrdtool.update(self.fname(self.path, hostid, ds_name), *values)


class LastSecond(object):
    _second = 0

    def __init__(self, path, table):
        self.fname = os.path.join(path, '%s.last_second' % table)
    
    def get_second(self):
        try:
            with open(self.fname, 'r') as f:
                try:
                    self._second = int(f.read())
                except ValueError, e:
                    pass
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
            CONSUMER_LOG.exception(
                'Can\'t open last second file %s: %s' % (
                    self.fname, str(e)))
    second = property(get_second, set_second)


class ZabbixConsumer(object):
    def __init__(self, db, path):
        self.db, self.path = db, path
        

    def get_data(self, hostids):
        """Read data appeared since last time it was read.

        Data is separated by items.
        Objects to call after data is sucessfully handled returned as well.
        They save time of the lookup.
        """
        # for each table history, history_uint
        #   get last second
        #   for every itemid designated by key_
        #     get everything after the last second
        #   return collected data, objects to commit last seconds and delays
        data = {}
        second_savers = {}
        items_2_delays = {}
        cursor = self.db.cursor()
	sql = ('SELECT itemid, value_type, delay ' +
              'FROM items ' +	
              'WHERE hostid IN (%s) AND key_ IN (%s)') % (
                ','.join(map(str, hostids)), ITEMS_KEYS)
	CONSUMER_LOG.info(ITEMS_KEYS)
	CONSUMER_LOG.info(sql)
        cursor.execute(sql)
        for itemid, value_type, delay in cursor.fetchall():
            items_2_delays[itemid] = delay
            table = ITEM_VALUE_TYPE_2_TABLE_NAME[value_type]
            if itemid not in second_savers:
                second_savers[itemid] = LastSecond(self.path, itemid)
            last_sec = second_savers[itemid]
            cursor.execute('SELECT itemid, clock, value '
                           'FROM %s WHERE clock > %%s AND itemid = %%s '
                           'ORDER BY clock' % table,
                           (last_sec.second, itemid))
            data[itemid] = [x[1:] for x in cursor.fetchall()]
            if len(data[itemid]):
                last_sec.second = data[itemid][-1][0]
        cursor.close()
        return data, second_savers.values(), items_2_delays

    def get_hosts(self):
        cursor = self.db.cursor()
        cursor.execute('SELECT hostid, host FROM hosts WHERE status <> 3')
        data = cursor.fetchall()
        hostids = [x[0] for x in data]
        hosts = [x[1] for x in data]
        items_2_hosts = {}
        items_2_keys = {}
        cursor.execute('SELECT itemid, items.hostid, key_ '
                       'FROM items JOIN hosts ON (items.hostid = hosts.hostid) '
                       'WHERE key_ IN (%s)' % (ITEMS_KEYS,))
        for itemid, hostid, key_ in cursor.fetchall():
            items_2_hosts[itemid] = hostid
            items_2_keys[itemid] = key_
        cursor.close()
        return hostids, items_2_hosts, items_2_keys


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
            time.sleep(10)

    def consume(self):
        CONSUMER_LOG.info('1')
        with open(os.path.join(self.path, 'consume.lock'), 'w') as fd:
            CONSUMER_LOG.info('2')
            fcntl.lockf(fd, fcntl.LOCK_EX)        
            CONSUMER_LOG.info('3')
            with Locker('Locker', (), {})().lock:
                CONSUMER_LOG.info('Consuming now in %s.' % os.getpid())
                while True:
                    self.reconnect()
                    try:
                        z = ZabbixConsumer(self.db, self.path)
                        r = RRDKeeper(self.path)
                        # get hosts and items
                        hostids, items_2_hosts, items_2_keys = z.get_hosts()
                        CONSUMER_LOG.info(hostids)
                        CONSUMER_LOG.info(items_2_keys)
                        # get historic data
                        data, second_savers, items_2_delays = z.get_data(hostids)
                        CONSUMER_LOG.info(data)
                        # save data in rrd
                        r.update(data, items_2_hosts,
                            items_2_keys, items_2_delays)
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
    return flask.jsonify(versions=[url('discover', version='0')])


@app.route('/v<version>/')
def discover(version):
    if version == '0':
        return flask.jsonify(
            version=version,
            endpoints={
                'hosts': url('hosts', version=version),
                'periods': url('periods', version=version),
                'parameters': url('parameters', version=version),
                'data': '%s?parameters=param1,param2' % url('data', 
                            version=version, 
                            host='_host_',
                            period='_period_'),
                'hosts_statuses': url('hosts_statuses', version=version) 
                }
            )
    flask.abort(404)


def _hosts(version):
    if version == '0':
        path = os.path.abspath(flask.current_app.config['ZABBIX_PROXY_TMP'])
        hostids = []
        for fname in [x for x in os.listdir(path) if x.endswith('.rrd')]:
            if '.' in fname:
                try:
                    hostids.append(int(fname.split('.')[0]))
                except ValueError:
                    pass
        db = MySQLdb.connect(**app.config['ZABBIX_PROXY_DB'])
        c = db.cursor()
        c.execute('SELECT host FROM hosts WHERE hostid IN (%s)' % ', '.join([str(x) for x in hostids]))
        hosts = [x[0] for x in c.fetchall()]
        c.close()
        return hosts
    raise RuntimeError, 'Unknown version'


@app.route('/v<version>/hosts/')
def hosts(version):
    if version == '0':
        return flask.jsonify(hosts=_hosts(version))
    flask.abort(404)


@app.route('/v<version>/periods/') 
def periods(version):
    if version == '0':
        return flask.jsonify(periods=PERIODS)
    flask.abort(404)


@app.route('/v<version>/parameters/')
def parameters(version):
    if version == '0':
        return flask.jsonify(parameters=PARAMETERS)
    flask.abort(404)


@app.route('/v<version>/<host>/<period>/')
def data(version, host, period):
    if version == '0':
        if host not in _hosts(version):
            flask.abort(404)

        if period not in PERIODS:
            flask.abort(404)
        parameters = flask.request.args.get('parameters', None)
        if parameters is not None:
            parameters = parameters.split(',')
            for i in parameters:
                if i not in PARAMETERS:
                    flask.abort(404)
        else:
            parameters = PARAMETERS
        data_format = flask.request.args.get('format', 'png')
        if data_format not in ['png']:
            flask.abort(404)
        RESOLUTIONS = {
            '6h': 6 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH,
            '1d': 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH,
            '1w': 7 * 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH,
            '1m': 30 * 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH, 
            '1y': 365 * 24 * 60 * 60 / RRDKeeper.POINTS_PER_GRAPH
            }
        if data_format == 'png':
            width = flask.request.args.get('width', 400)
            height = flask.request.args.get('height', 400)
            img_file = tempfile.NamedTemporaryFile(mode='rb', dir='/tmp')
            args = [img_file.name, 
                    '--start', 'end-%s' % period, 
                    '--step', RESOLUTIONS[period], 
                    '-h', height, 
                    '-w', width]
            if 'title' in flask.request.args:
                args.extend(['--title', flask.request.args['title']])
            db = MySQLdb.connect(**app.config['ZABBIX_PROXY_DB'])
            c = db.cursor()
            c.execute('SELECT hostid FROM hosts WHERE host = %s', [host])
            r = c.fetchone()
            if r is None:
                flask.abort(404)
            hostid = r[0]
            for i, ds_name in enumerate(parameters):
                fname = RRDKeeper.fname(
                    os.path.abspath(
                        flask.current_app.config['ZABBIX_PROXY_TMP']),
                    str(hostid),
                    ds_name)
                if os.path.exists(fname):
                    args.extend([
                            'DEF:%s=%s:%s:AVERAGE' % (ds_name, fname, ds_name),
                            'LINE1:%s#%s:"%s"' % (ds_name, COLORS[i], ds_name)])
            args = map(str, args)
            rrdtool.graph(*args)
            response = flask.make_response(img_file.read())
            img_file.close()
            response.headers['Content-Type'] = 'image/png'
            return response
    flask.abort(404)


def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


@app.route('/v<version>/hosts_statuses/')
def hosts_statuses(version):
    """Return list of hosts with statuses.

    Decision on host status here is based on timedelta between last of last second for any host's item and now. If it is bigger then 3 minutes host is off.
 
    Can cause problems on client if some host gets deleted between fetching /hosts/ and /hosts_statuses/. Currently we do not clean old hosts at all and this is not a problem, though it can become it after we start cleaning.

    {"host_statuses: [["n006", 0], ["n007", 1]]}
    """
    if version == '0':
        AVAILABLE_DUE = 3 * 60
        ON = 0
        OFF = 1

        hosts = _hosts(version)
        db = MySQLdb.connect(**app.config['ZABBIX_PROXY_DB'])
        c = db.cursor()
        
        NOW = datetime.datetime.utcnow()
        result = []

        for host in hosts:
            seconds = []
            c.execute("SELECT hostid FROM hosts WHERE host = %s", (host,))
            r = c.fetchone()
            if r is None:
                continue
            hostid = r[0]
            c.execute("SELECT itemid FROM items WHERE hostid = %s", (hostid,))
            items = c.fetchall()
            for (itemid,) in items:
                last_second = LastSecond(
                    flask.current_app.config['ZABBIX_PROXY_TMP'],
                    itemid)
                seconds.append(last_second.second)
            status = OFF
            if len(seconds):
                last_datetime = datetime.datetime.utcfromtimestamp(max(seconds))
                if total_seconds(NOW - last_datetime) < AVAILABLE_DUE:
                    status = ON
            result.append([host, status])
        db.close()
        return flask.jsonify(hosts_statuses=result)
    flask.abort(404)
