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


# TODO(apugachev) consider converting this staff to storm models
import functools

import flask

from focus.models import orm


def prepare_database_connection(func):
    """Create Storm ORM Store if it does not exist yet."""
    @functools.wraps(func)
    def _wrapped(*args, **kwargs):
        if not hasattr(flask.g, 'inv_store'):
            flask.g.inv_store = orm.get_store('INVITATIONS')
        return func(*args, **kwargs)
    return _wrapped


@prepare_database_connection
def save_invitation(email, hash_code, role):
    flask.g.inv_store.execute(
        'INSERT INTO invitations SET '
        'email = ?, hash = ?, complete = ?, role = ?',
        (email, hash_code, 0, role))
    flask.g.inv_store.commit()


@prepare_database_connection
def get_invitation_by_hash(invitation_hash):
    return flask.g.inv_store.execute(
        'SELECT * FROM invitations '
        'WHERE invitations.hash = ?',
        (invitation_hash, )).get_one()


@prepare_database_connection
def update_invitation(invitation_id, email, hash_code):
    flask.g.inv_store.execute(
        'UPDATE invitations SET '
        'email = ?, hash = ?, complete = ? '
        'WHERE id = ?',
        (email, hash_code, 1, invitation_id))
    flask.g.inv_store.commit()


@prepare_database_connection
def get_masks():
    return flask.g.inv_store.execute(
        'SELECT email_mask FROM email_masks').get_all()


@prepare_database_connection
def save_recovery(email, hash_code, complete):
    flask.g.inv_store.execute(
        'INSERT INTO recovery_requests SET '
        'email = ?, hash = ?, complete = ?',
        (email, hash_code, complete))
    flask.g.inv_store.commit()


@prepare_database_connection
def get_recovery_request_by_hash(recovery_hash):
    return flask.g.inv_store.execute(
        'SELECT * FROM recovery_requests '
        'WHERE recovery_requests.hash = ?', (recovery_hash,)).get_one()


@prepare_database_connection
def get_configured_hostname():
    try:
        result = flask.g.inv_store.execute('SELECT hostname FROM configured_hostnames').get_one()
        if result:
            return result[0]
        else:
            return flask.current_app.config.get('CONFIGURED_HOSTNAME', '')
    except TypeError, e:
        # to not be lost in WTForms
        raise RuntimeError, str(e)


@prepare_database_connection
def set_configured_hostname(hostname):
    flask.g.inv_store.execute('DELETE FROM configured_hostnames')
    flask.g.inv_store.execute('INSERT INTO configured_hostnames (hostname) VALUES (?)', (hostname,))
    flask.g.inv_store.commit()
