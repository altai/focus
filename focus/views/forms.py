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


# TODO(apugachev) convert factories to plain classes where possible

import decimal
import urlparse

import netaddr

import flask
from flaskext import wtf
from flaskext.wtf import html5
from focus.views import utils
from focus import clients
from focus.models import row_mysql_queries


def get_login_form():
    """
    Return login form class with correct default value of "next".
    """
    class LoginForm(wtf.Form):
        next = wtf.HiddenField(default=utils.get_next_url())
        login = wtf.TextField('Login or e-mail', [wtf.Required()])
        password = wtf.PasswordField('Password', [wtf.Required()])

        def validate_csrf_token(self, field):
            field.data = str(field.data)
            super(LoginForm, self).validate_csrf_token(field)

    return LoginForm


def get_spawn_form(images, flavors, security_groups, key_pairs):
    """
    Return form class.

    Get real values for selects to present real data for user to select.
    Validation won't pass later if you won't supply real data for form
    validating user input.
    """
    l_id_name = lambda x: (str(x.id), x.name)
    l_by_name = lambda x: x[1]
    l_flavor = lambda x: (x.disk, x.ram, x.vcpus)
    IMAGE_CHOICES = sorted(
        map(lambda x: (x.id, x.name), images), key=l_by_name)
    FLAVOR_CHOICES = map(l_id_name, sorted(flavors, key=l_flavor))
    SECURITY_GROUP = sorted(map(lambda x: (x.name, x.name), security_groups), 
                            key=l_by_name)
    KEYPAIR_CHOICES = list(sorted(
	map(lambda x: (x.name, x.name), key_pairs),
	key=l_by_name))
    KEYPAIR_CHOICES.insert(0, ('', ''))


    class SpawnForm(wtf.Form):
        image = wtf.SelectField(
            'Image', [wtf.Required()], choices=IMAGE_CHOICES)
        flavor = wtf.SelectField(
            'Flavor', [wtf.Required()], choices=FLAVOR_CHOICES)
        name = wtf.TextField('Name', [wtf.Required()])
        password = wtf.PasswordField('Password')
        confirm_password = wtf.PasswordField(
            'Confirm Password', [wtf.EqualTo('password')])
        keypair = wtf.SelectField('Key Pair', choices=KEYPAIR_CHOICES)
        security_groups = wtf.SelectMultipleField(
            'Security Groups', choices=SECURITY_GROUP)

    return SpawnForm


def get_new_user_to_project_form(users, roles):
    USERS_CHOICES = [(x.id, x.name) for x in users]
    ROLES_CHOICES = [(x.id, x.name) for x in roles]

    class NewUserToProjectForm(wtf.Form):
        user = wtf.SelectField(
            'User', [wtf.Required()], choices=USERS_CHOICES, coerce=int)
        roles = wtf.SelectMultipleField(
            'Roles', [wtf.Required()], choices=ROLES_CHOICES, coerce=int)
    return NewUserToProjectForm


class CreateSSHKey(wtf.Form):
    # TODO(apugachev) look in nova for boundaries
    name = wtf.TextField('Name of keypair', [wtf.Required()])
    public_key = wtf.TextField(
        'Public Key', [wtf.Optional()],
        description='Can be omitted. New keypair will be generated')


class NewImage(wtf.Form):
    name = wtf.TextField('Image name', [wtf.Required()])
    upload_type = wtf.SelectField(
        'Upload type', [wtf.Required()],
        choices=(('', 'Single'), ('separate', 'Composite')))


class DeleteUserForm(wtf.Form):
    user_id = wtf.HiddenField('user id', [wtf.Required()])


class AddUserToProject(wtf.Form):
    add_project = wtf.SelectField('Projects', [wtf.Required()], choices=[])
    user = wtf.HiddenField('User', [wtf.Required()])


class RemoveUserFromProject(wtf.Form):
    remove_project = wtf.SelectField('Projects', [wtf.Required()], choices=[])
    user = wtf.HiddenField('User', [wtf.Required()])


class DeleteForm(wtf.Form):
    """Just an empty form to easily bypass CSRF checks."""

class DecimalFieldRequired(wtf.Required):
    """
    Validates that the field contains data. This validator will stop the
    validation chain on error.

    If the data is empty, also removes prior errors (such as processing errors)
    from the field.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __call__(self, form, field):
        if not field.data == decimal.Decimal('0.0'):
            if (
                not field.data or isinstance(field.data, basestring) and 
                not field.data.strip()):
                    if self.message is None:
                        self.message = field.gettext(u'This field is required.')

                    field.errors[:] = []
                    raise StopValidation(self.message)



class TariffEditForm(wtf.Form):
    price = wtf.DecimalField(
        'Price',
        [DecimalFieldRequired()],
        places=None)
    migrate = wtf.BooleanField(
        'Migrate Resources',
        description='''
Should all currently charging resources migrate to the new tariffs''')


class PasswordRecoveryRequest(wtf.Form):
    email = wtf.html5.EmailField('Email', [wtf.Required()])


class NewProject(wtf.Form):
    name = wtf.TextField('Name', [wtf.Required()])
    description = wtf.TextField('Description')
    network = wtf.SelectField(
        'Network', [wtf.Required()], choices=[],
        description='Network label, CIDR, VLAN respectively')

# TODO: contorl networksize >= 4
class CreateNetwork(wtf.Form):
    cidr = wtf.TextField('CIDR', [wtf.Required()])
    vlan = wtf.IntegerField('VLAN', [wtf.NumberRange(min=1, max=4096, 
        message='Not in range %(min)s - %(max)s')])

    def validate_cidr(form, field):
        try:
            network = netaddr.IPNetwork(field.data)
        except (UnboundLocalError, netaddr.AddrFormatError):
            raise wtf.ValidationError('Unrecognised format of CIDR')
        if network.size < 4:
            raise wtf.ValidationError('Network size is lower then 4; use something like 10.1.1.1/30.')
        if network.size > 65536:
            raise wtf.ValidationError('Network size is greater then 65536')


class SecurityGroupCreate(wtf.Form):
    name = wtf.TextField('Name', [wtf.Required()])
    description = wtf.TextField('Description', [wtf.Required()])


class SecurityGroupRuleAdd(wtf.Form):
    ip_protocol = wtf.SelectField(
        'IP Protocol',
        choices=[('tcp', 'TCP'),
                 ('udp', 'UDP'),
                 ('icmp', 'ICMP')])

    from_port = wtf.IntegerField(
        "From Port",
        validators=[wtf.NumberRange(min=-1, max=65536)])

    to_port = wtf.IntegerField(
        "To Port",
        validators=[wtf.NumberRange(min=-1, max=65536)])

    group_id = wtf.SelectField('Source Group', choices=[])
    cidr = wtf.TextField(
        "CIDR",
        default="0.0.0.0/0")

    def __init__(self, *args, **kwargs):
        security_group_id = kwargs.pop('security_group_id')
        super(SecurityGroupRuleAdd, self).__init__(*args, **kwargs)
        security_groups = (clients.user_clients(flask.g.tenant_id).compute.
                           security_groups.list())
        self.group_id.choices = [('<None>', '')] + [(str(sg.id), sg.name)
                                 for sg in security_groups
                                 if str(sg.id) != str(security_group_id)]


class CreateEmailMask(wtf.Form):
    email_mask = wtf.TextField(
        'Domain',
        [wtf.Required()],
        description='Domain part of allowed emails for invitations')


# TODO(apugachev) check if this role is passed to keystone;
# if yes, take from settings
ROLES = (
    ('user', 'User'),
    ('admin', 'Global Admin')
)


class Invite(wtf.Form):
    email = html5.EmailField('Email', [wtf.Required()])
    role = wtf.SelectField(u'Role', choices=ROLES)


class InviteRegister(wtf.Form):
    username = wtf.TextField('Username', [wtf.Required()])
    password = wtf.PasswordField('Password', [wtf.Required()])


def validate_hostname(form, field):
    m = urlparse.urlparse(field.data)
    if m.scheme and m.scheme not in ['http', 'https']:
        raise wtf.ValidationError('Forbidden protocol: %s' % m.scheme)
    if not m.netloc:
        raise wtf.ValidationError('Hostname required')


def filter_hostname(x):
    if '://' not in x:
        x = 'http://' + x
    m = urlparse.urlparse(x)
    return urlparse.urlunsplit((m.scheme or 'http', m.netloc, '', '', ''))



class ConfigureHostnameForm(wtf.Form):
    hostname = wtf.TextField(
        u'Focus URL',
        [wtf.Required(), validate_hostname],
        [filter_hostname],
        default=row_mysql_queries.get_configured_hostname)
