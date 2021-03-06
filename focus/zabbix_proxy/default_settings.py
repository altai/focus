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


ZABBIX_PROXY_DB = {
    'host': 'localhost',
    'user': 'root',
    'db': 'zabbix'
}

ZABBIX_PROXY_TMP = '/var/lib/focus'
ZABBIX_LOG_FILE = '/var/log/focus/zabbix_proxy.log'
ZABBIX_LOG_MAX_BYTES = 1024 * 1024 * 100
ZABBIX_LOG_BACKUP_COUNT = 12
