from flaskext.wtf import Form, Required, PasswordField, HiddenField
from flaskext.wtf.html5 import EmailField

class InviteForm(Form):
    email = EmailField('Email', [Required()])

class InviteRegisterForm(Form):
    email = HiddenField()
    password = PasswordField('Password', [Required()])