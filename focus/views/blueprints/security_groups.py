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


"""Provides factory of blueprints for security group management.
"""

import flask
from flask import blueprints

from focus import clients
from focus import utils
from focus.views import environments
from focus.views import forms
from focus.views import pagination


from openstackclient_base import exceptions


def get_bp(blueprint_name):
    """Return blueprint for Security_Group management."""
    bp = blueprints.Blueprint(blueprint_name, __name__)

    @bp.route('<security_group_id>/', methods=['GET'])
    def show(security_group_id, add_form=None):
        """Present details page for single security group object.
        """
        security_group = (clients.user_clients(flask.g.tenant_id).compute.
                          security_groups.get(security_group_id))
        def prepare_rule_for_modal(rule):
            return (rule, dict(id=rule['id'],
                               name="%s[%s-%s]/%s@%s" % (rule['ip_protocol'],
                                                         rule['from_port'],
                                                         rule['to_port'],
                                                         security_group.name,
                                                         rule['ip_range']['cidr'])))
        security_group_rules = map(prepare_rule_for_modal, security_group.rules)
        return {
            'security_group_rules': security_group_rules,
            'security_group': security_group,
            'add_form': add_form or forms.SecurityGroupRuleAdd(
                security_group_id=security_group_id),
            'delete_form': forms.DeleteForm(),
            'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
            'subtitle': 'Security group details',
        }

    @bp.route('')
    def index():
        """List security groups.
        """
        security_groups = (clients.user_clients(flask.g.tenant_id).compute.
                           security_groups.list())
        p = pagination.Pagination(security_groups)
        data = p.slice(security_groups)
        return {
            'security_groups': data,
            'pagination': p,
            'delete_form': forms.DeleteForm(),
            'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
            'subtitle': 'List of existing security groups'
        }

    @bp.route('new/', methods=['GET', 'POST'])
    def new():
        """Create security_group.
        """
        form = forms.SecurityGroupCreate()
        if form.validate_on_submit():
            try:
                security_group = (clients.user_clients(flask.g.tenant_id).
                                  compute.security_groups.create(
                        name=form.name.data,
                        description=form.description.data))
            except exceptions.HttpException as ex:
                flask.flash(ex.message, 'error')
            else:
                flask.flash('Security group %s created.' % form.name.data,
                            'success')
                return flask.redirect(flask.url_for('.index'))
        return {
            'form': form,
            'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
            'subtitle': 'Add new security group'
        }

    @bp.route('<security_group_id>/delete/', methods=['POST'])
    def delete(security_group_id):
        form = forms.DeleteForm()
        if form.validate_on_submit():
            try:
                (clients.user_clients(flask.g.tenant_id).
                 compute.security_groups.delete(security_group_id))
            except exceptions.HttpException as ex:
                flask.flash(ex.message, 'error')
            else:
                flask.flash('Security group successfully deleted',
                            'success')
        else:
            flask.flash('Invalid form', 'error')
        return flask.redirect(flask.url_for('.index'))

    @bp.route('<security_group_id>/<rule_id>/delete', methods=['POST'])
    def delete_rule(security_group_id, rule_id):
        form = forms.DeleteForm()
        if form.validate_on_submit():
            (clients.user_clients(flask.g.tenant_id).
             compute.security_group_rules.delete(rule_id))
            flask.flash('Security group rule successfully deleted', 'success')
        else:
            flask.flash('Invalid form', 'error')
        return flask.redirect(flask.url_for(
                '.show', security_group_id=security_group_id))

    @bp.route('<security_group_id>/add_rule', methods=['GET', 'POST'])
    def add_rule(security_group_id):
        form = forms.SecurityGroupRuleAdd(security_group_id=security_group_id)
        if form.validate_on_submit():
            try:
                group_id = int(form.group_id.data)
                cidr = None
            except ValueError:
                group_id = None
                cidr = form.cidr.data
            try:
                (clients.user_clients(flask.g.tenant_id).
                 compute.security_group_rules.create(
                        security_group_id,
                        form.ip_protocol.data,
                        form.from_port.data,
                        form.to_port.data,
                        cidr,
                        group_id))
            except exceptions.HttpException as ex:
                flask.flash(ex.message, 'error')
            else:
                flask.flash('Security group rule successfully added',
                            'success')
                return flask.redirect(flask.url_for(
                        '.show', security_group_id=security_group_id))

        return {
            'form': form,
            'security_group_id': security_group_id,
            'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
            'subtitle': 'Add new rule'
        }

    return bp


PBP = environments.project(get_bp('project_security_groups'))
