# coding=utf-8
from flask import g

from C4GD_web.models.orm import User, Role

from flaskext.wtf import Form, HiddenField, TextField, PasswordField, Required,\
    SelectField, EqualTo, SelectMultipleField

from storm.locals import Not

from .utils import get_next_url



def get_login_form():
    """
    Return login form class with correct default value of "next".
    """
    class LoginForm(Form):
        next = HiddenField(default=get_next_url())
        username = TextField('Username', [Required()])
        password = PasswordField('Password', [Required()])
    return LoginForm


def get_spawn_form(images, flavors, security_groups, key_pairs):
    """
    Return form class.

    Get real values for selects to present real data for user to select.
    Validation won't pass later if you won't supply real data for form 
    validating user input.
    """
    l1 = lambda x: (x['id'], x['name'])
    l2 = lambda x: (x['name'], x['name'])
    l3 = lambda x: x[1]
    l4 = lambda x: (x['keypair']['name'], x['keypair']['name'])
    IMAGE_CHOICES = sorted(map(l1, images), key=l3)
    FLAVOR_CHOICES = sorted(map(l1, flavors), key=l3)
    SECURITY_GROUP = sorted(map(l1, security_groups), key=l3)
    KEYPAIR_CHOICES = sorted(map(l4, key_pairs), key=l3)   

    class SpawnForm(Form):
        image = SelectField('Image', [Required()], choices=IMAGE_CHOICES)
        flavor = SelectField('Flavor', [Required()], choices=FLAVOR_CHOICES, coerce=int)
        name = TextField('Name', [Required()])
        password = PasswordField('Password')
        confirm_password = PasswordField('Confirm Password', [EqualTo('password')])
        keypair = SelectField('Key Pair', choices=KEYPAIR_CHOICES)
        security_groups = SelectMultipleField('Security Groups', choices=SECURITY_GROUP, coerce=int)

    return SpawnForm

def get_new_user_to_project_form(users, roles):
    USERS_CHOICES = [(x.id, x.name) for x in users]
    ROLES_CHOICES = [(x.id, x.name) for x in roles]
    class NewUserToProjectForm(Form):
        user = SelectField(
            'User', [Required()], choices=USERS_CHOICES, coerce=int)
        roles = SelectMultipleField(
            'Roles', [Required()], choices=ROLES_CHOICES, coerce=int)
    return NewUserToProjectForm
