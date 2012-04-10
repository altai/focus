from flask import g
from flaskext.wtf import Form, HiddenField, TextField, PasswordField, Required,\
    SelectField, EqualTo, SelectMultipleField
from C4GD_web import app
from utils import get_next_url
from models import Image, Flavor, KeyPair, SecurityGroup


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
    IMAGE_CHOICES = [(x.id, x.name) for x in g.pool(Image.list)]
    FLAVOR_CHOICES = [(x.id, x.name) for x in g.pool(Flavor.list)]
    KEYPAIR_CHOICES = [(x.name, x.name) for x in g.pool(KeyPair.list)]
    SECURITY_GROUP = [(x.id, x.name) for x in g.pool(SecurityGroup.list)]

    IMAGE_CHOICES = sorted(IMAGE_CHOICES, key=lambda x: x[1])
    FLAVOR_CHOICES = sorted(FLAVOR_CHOICES, key=lambda x: x[1])
    KEYPAIR_CHOICES = sorted(KEYPAIR_CHOICES, key=lambda x: x[1])
    SECURITY_GROUP = sorted(SECURITY_GROUP, key=lambda x: x[1])
    
    class SpawnForm(Form):
        image = SelectField('Image', [Required()], choices=IMAGE_CHOICES, coerce=int)
        flavor = SelectField('Flavor', [Required()], choices=FLAVOR_CHOICES, coerce=int)
        name = TextField('Name', [Required()])
        password = TextField('Password', [Required()])
        confirm_password = TextField('Confirm Password', [EqualTo('password')])
        keypair = SelectField('Key Pair', [Required()], choices=KEYPAIR_CHOICES)
        security_groups = SelectMultipleField('Security Groups', [Required()], choices=SECURITY_GROUP, coerce=int)

    return SpawnForm
    
