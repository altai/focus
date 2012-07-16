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

import netaddr

from flaskext import wtf
from flaskext.wtf import html5
from focus.views import utils


def get_login_form():
    """
    Return login form class with correct default value of "next".
    """
    class LoginForm(wtf.Form):
        next = wtf.HiddenField(default=utils.get_next_url())
        email = wtf.TextField('Email', [wtf.Required(), wtf.Email()])
        password = wtf.PasswordField('Password', [wtf.Required()])
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
    SECURITY_GROUP = sorted(map(l_id_name, security_groups), key=l_by_name)
    KEYPAIR_CHOICES = sorted(
        map(lambda x: (x.name, x.name), key_pairs),
        key=l_by_name)

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
    project = wtf.SelectField('Projects', [wtf.Required()], choices=[])
    user = wtf.HiddenField('User', [wtf.Required()])


class RemoveUserFromProject(wtf.Form):
    project = wtf.SelectField('Projects', [wtf.Required()], choices=[])
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


class CreateNetwork(wtf.Form):
    cidr = wtf.TextField('CIDR', [wtf.Required()])
    vlan = wtf.IntegerField(
        'VLAN',
        [wtf.Required(),
         wtf.NumberRange(min=1, max=4096, message='Invalid VLAN')])

    def validate_cidr(form, field):
        try:
            network = netaddr.IPNetwork(field.data)
        except (UnboundLocalError, netaddr.AddrFormatError):
            raise wtf.ValidationError('Unrecognised format of CIDR')
        if network.size > 65536:
            raise wtf.ValidationError('Network size is greater then 65536')


class CreateEmailMask(wtf.Form):
    email_mask = wtf.TextField(
        'Domain',
        [wtf.Required()],
        description='Domain part of allowed emails for invitations')


# TODO(apugachev) check if this role is passed to keystone;
# if yes, take from settings
ROLES = (
    ('admin', 'Global Admin'),
    ('user', 'User'),
)


class Invite(wtf.Form):
    email = html5.EmailField('Email', [wtf.Required()])
    role = wtf.SelectField(u'Role', choices=ROLES)


class InviteRegister(wtf.Form):
    email = wtf.HiddenField()
    username = wtf.HiddenField()
    password = wtf.PasswordField('Password', [wtf.Required()])