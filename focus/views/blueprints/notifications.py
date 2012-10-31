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

import urllib

import flask
from flask import blueprints
from flaskext import wtf

from focus import utils

from focus.views import environments
from focus.views import forms
from focus.views import pagination

from openstackclient_base.exceptions import HttpException


bp = environments.admin(blueprints.Blueprint('notifications', __name__))


class CreateNotification(wtf.Form):
    name = wtf.SelectField('Name', [wtf.Required()], choices=[])
    is_minimized = wtf.BooleanField('Is minimized')

    def __init__(self, *args, **kwargs):
        super(CreateNotification, self).__init__(*args, **kwargs)
        parameters = utils.notifications_api_call("/parameter")
        item_list = utils.notifications_api_call("/item")
        created_keys = set([par["key_"] for par in parameters])
        choices_dict = dict(((item["key_"], item["name"])
                             for item in item_list
                             if item["key_"] not in created_keys))
        self.name.choices = sorted(choices_dict.iteritems(),
                                   key=lambda i: i[1])


class EditNotification(wtf.Form):
    is_minimized = wtf.BooleanField('Is minimized')


class EditParameter(wtf.Form):
    is_notified = wtf.BooleanField('Is notified')
    addressees = wtf.TextField('Addressees')
    bound = wtf.FloatField('Bound')
    hysteresis = wtf.FloatField('Hysteresis')
    threshold = wtf.IntegerField(
        'Threshold',
        [wtf.NumberRange(min=0, max=100,
        message='Not in range %(min)s - %(max)s')])


class DictObject(object):
    def __init__(self, dic):
        self.dic = dic

    def __getattr__(self, key):
        return self.dic[key]


def notification_normalize(obj):
    try:
        obj["addressees"] = ",".join(obj["addressees"])
    except:
        obj["addressees"] = ""
    for key in "bound", "threshold", "hysteresis":
        obj[key] = obj[key] or 0


@bp.route('')
def index():
    try:
        notifications = utils.notifications_api_call("/parameter")
    except HttpException as ex:
        notifications = []
    item_list = utils.notifications_api_call("/item")
    item_by_key = dict(((item["key_"], item) for item in item_list))
    for notif in notifications:
        notification_normalize(notif)
        try:
            notif["name"] = item_by_key[notif["key_"]]["name"]
        except KeyError:
            notif["name"] = notif["key_"]
    notifications = sorted(notifications,
                           key=lambda n: (n["is_email"], n["name"]))
    p = pagination.Pagination(len(notifications))
    offset = p.limit_offset()
    notifications = notifications[offset[0]:offset[1]]
    return {
        'objects': notifications,
        'pagination': p,
        'delete_form': forms.DeleteForm(),
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'List of notifications'
    }


@bp.route('parameter/<object_id>/', methods=['GET', 'POST'])
def parameter_edit(object_id):
    try:
        obj = utils.notifications_api_call(
            "/parameter", params={"id": object_id})[0]
    except IndexError:
        flask.abort(404)
    notification_normalize(obj)
    form = EditParameter(obj=DictObject(obj))
    if form.validate_on_submit():
        body = dict(
            ((key, getattr(form, key).data)
             for key in ("is_notified", "bound", "hysteresis", "threshold")))
        body["addressees"] = [addr.strip()
                              for addr in form.addressees.data.split(",")]
        try:
            utils.notifications_api_call(
                "/parameter/%s" % object_id, body=body, method="PUT")
        except HttpException as ex:
            flask.flash(ex.message, 'error')
        else:
            flask.flash('Notification is updated.', 'success')
            return flask.redirect(flask.url_for('.index'))
    item_list = utils.notifications_api_call(
        "/item", params={"key_": obj["key_"]})
    try:
        notif_name = item_list[0]["name"]
    except (IndexError, KeyError):
        notif_name = obj["key_"]
    return {
        'form': form,
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Edit %s notification for %s' %
        ("e-mail" if obj["is_email"] else "SMS", notif_name),
    }


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Create a notification.

    """
    form = CreateNotification()
    if form.validate_on_submit():
        try:
            body = {
                "key_": form.name.data,
                "is_minimized": form.is_minimized.data
            }
            utils.notifications_api_call(
                "/item_info", body=body, method="POST")
        except HttpException as ex:
            flask.flash(ex.message, 'error')
        else:
            flask.flash('Notification has been created.', 'success')
            return flask.redirect(flask.url_for('.index'))
    return {
        'form': form,
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Add a new notification'
    }


@bp.route('<path:key_>/', methods=['GET', 'POST'])
def show(key_):
    try:
        obj = utils.notifications_api_call(
            "/item_info", params={"key_": key_})[0]
    except IndexError:
        flask.abort(404)
    form = EditNotification(obj=DictObject(obj))
    if form.validate_on_submit():
        body = {"is_minimized": form.is_minimized.data}
        try:
            utils.notifications_api_call(
                "/item_info/%s" % obj["id"], body=body, method="PUT")
        except HttpException as ex:
            flask.flash(ex.message, 'error')
        else:
            flask.flash('Notification is updated.', 'success')
            return flask.redirect(flask.url_for('.index'))
    item_list = utils.notifications_api_call(
        "/item", params={"key_": obj["key_"]})
    try:
        notif_name = item_list[0]["name"]
    except (IndexError, KeyError):
        notif_name = obj["key_"]
    return {
        'form': form,
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Edit notification for %s' % notif_name,
    }


@bp.route('delete/<path:key_>/', methods=['POST'])
def delete(key_):
    form = forms.DeleteForm()
    if form.validate_on_submit():
        try:
            utils.notifications_api_call(
                "/item_info/%s" % urllib.quote(key_, safe=''),
                method="DELETE")
        except HttpException as ex:
            flask.flash(ex.message, 'error')
        else:
            flask.flash('Notification is deleted.', 'success')
    return flask.redirect(flask.url_for('.index'))
