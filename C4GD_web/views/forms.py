# coding=utf-8
from flask import g
from flaskext.wtf import Form, HiddenField, TextField, PasswordField, Required,\
    SelectField, EqualTo, SelectMultipleField

from C4GD_web import app
from C4GD_web.models import Image, Flavor, KeyPair, SecurityGroup

from utils import get_next_url


def get_login_form():
    """
    Creates login form class with correct default value of "next".
    
    Context: view
    """
    class LoginForm(Form):
        next = HiddenField(default=get_next_url())
        username = TextField('Username', [Required()])
        password = PasswordField('Password', [Required()])
    return LoginForm

def get_spawn_form():
    IMAGE_CHOICES, FLAVOR_CHOICES, KEYPAIR_CHOICES, SECURITY_GROUP = g.pool(
        [Image.list, Flavor.list, KeyPair.list, SecurityGroup.list])
    l1 = lambda x: (x.id, x.name)
    l2 = lambda x: (x.name, x.name)
    l3 = lambda x: x[1]
    IMAGE_CHOICES = sorted(map(l1, IMAGE_CHOICES), key=l3)
    FLAVOR_CHOICES = sorted(map(l1, FLAVOR_CHOICES), key=l3)
    SECURITY_GROUP = sorted(map(l1, SECURITY_GROUP), key=l3)
    KEYPAIR_CHOICES = sorted(map(l2, KEYPAIR_CHOICES), key=l3)   
    class SpawnForm(Form):
        image = SelectField('Image', [Required()], choices=IMAGE_CHOICES, coerce=int)
        flavor = SelectField('Flavor', [Required()], choices=FLAVOR_CHOICES, coerce=int)
        name = TextField('Name', [Required()])
        password = PasswordField('Password')
        confirm_password = PasswordField('Confirm Password', [EqualTo('password')])
        keypair = SelectField('Key Pair', choices=KEYPAIR_CHOICES)
        security_groups = SelectMultipleField('Security Groups', choices=SECURITY_GROUP, coerce=int)

    return SpawnForm


class NewUserToProjectForm(Form):
    def __init__(self, user):
        from C4GD_web.models.orm import User, Role
        from storm.locals import Not
        users = g.store.find(User, Not(User.id.is_in(g.tenant.users.find().config(distinct=True).values(User.id)))).\
            config(distinct=True).order_by('name')
        user_choices = [(x.id, x.name) for x in users]
        self.user.kwargs['choices'] = user_choices
        roles = g.store.find(Role).order_by('name')
        roles_choices = [(x.id, x.name) for x in roles]
        self.roles.kwargs['choices'] = roles_choices
        super(NewUserToProjectForm, self).__init__()
    user = SelectField('User', [Required()], coerce=int)
    roles = SelectMultipleField('Roles', [Required()], coerce=int)
        
