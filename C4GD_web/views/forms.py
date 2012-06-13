# coding=utf-8
from flask import g

from flaskext import wtf

import utils


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
    l_id_name = lambda x: (x['id'], x['name'])
    l_by_name = lambda x: x[1]
    IMAGE_CHOICES = sorted(
        map(lambda x: (x.id, x.name), images), key=l_by_name)
    FLAVOR_CHOICES = sorted(map(l_id_name, flavors), key=l_by_name)
    SECURITY_GROUP = sorted(map(l_id_name, security_groups), key=l_by_name)
    KEYPAIR_CHOICES = sorted(
        map(lambda x: (x['keypair']['name'], x['keypair']['name']), key_pairs),
        key=l_by_name)

    class SpawnForm(wtf.Form):
        image = wtf.SelectField('Image', [wtf.Required()], choices=IMAGE_CHOICES)
        flavor = wtf.SelectField('Flavor', [wtf.Required()], choices=FLAVOR_CHOICES)
        name = wtf.TextField('Name', [wtf.Required()])
        password = wtf.PasswordField('Password')
        confirm_password = wtf.PasswordField('Confirm Password', [wtf.EqualTo('password')])
        keypair = wtf.SelectField('Key Pair', choices=KEYPAIR_CHOICES)
        security_groups = wtf.SelectMultipleField('Security Groups', choices=SECURITY_GROUP)

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
    upload_type = wtf.SelectField('Upload type', [wtf.Required()], choices=(('', 'Single'), ('separate', 'Composite')))
    
    
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


class TariffEditForm(wtf.Form):
    price = wtf.DecimalField(
        'Price',
        [
            wtf.Required()
            ],
        places=None,
        description="USD/hour")
    migrate = wtf.BooleanField(
        'Migrate Resources',
        description="Whether all currently charging resources should migrate to\
 the new tariffs")

    
class PasswordRecoveryRequest(wtf.Form):
    email = wtf.html5.EmailField('Email', [wtf.Required()])


class NewProject(wtf.Form):
    name = wtf.TextField('Name', [wtf.Required()])
    description = wtf.TextField('Description')
