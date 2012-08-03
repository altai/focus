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


import flask
from flask import blueprints
from flaskext import principal

from focus.models import orm
from focus.views import forms
from focus.views import environments
from focus.views import pagination


bp = environments.admin(blueprints.Blueprint('invitation_domains', __name__))


@bp.before_request
def prepare():
    principal.Permission(('role', 'admin')).test()
    flask.g.store = orm.get_store('INVITATIONS')


@bp.route('')
def index():
    total_count = flask.g.store.execute(
        'SELECT count(*) from email_masks').get_one()[0]
    p = pagination.Pagination(total_count)
    rows = flask.g.store.execute(
        'SELECT * from email_masks ORDER BY email_mask LIMIT ?, ?',
        p.limit_offset()).get_all()
    objects = map(lambda row: dict(zip(('id', 'email_mask'), row)), rows)
    return {
        'pagination': p,
        'objects': objects,
        'delete_form': forms.DeleteForm(),
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Invitation domains list'
    }


@bp.route('delete/<object_id>/', methods=['POST'])
def delete(object_id):
    form = forms.DeleteForm()
    if form.validate_on_submit():
        flask.g.store.execute(
            'DELETE FROM email_masks WHERE id = ? LIMIT 1', (object_id,))
        flask.g.store.commit()
        flask.flash('Email mask removed.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {'form': form}


@bp.route('new/', methods=['GET', 'POST'])
def new():
    form = forms.CreateEmailMask()
    if form.validate_on_submit():
        flask.g.store.execute(
            'INSERT INTO email_masks (email_mask) VALUES (?)',
            (form.email_mask.data, ))
        flask.g.store.commit()
        flask.flash('Email mask created.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {
        'form': form,
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Add new email domain'
    }
