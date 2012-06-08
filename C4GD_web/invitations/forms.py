from flaskext.wtf import Form, Required, PasswordField, HiddenField, SelectField
from flaskext.wtf.html5 import EmailField


#+----+----------------------+------+------------+
#| id | name                 | desc | service_id |
#+----+----------------------+------+------------+
#|  1 | Admin                | NULL |       NULL |
#|  2 | Member               | NULL |       NULL |
#|  3 | KeystoneServiceAdmin | NULL |       NULL |
#|  4 | projectmanager       | NULL |       NULL |
#|  5 | cloudadmin           | NULL |       NULL |
#|  6 | itsec                | NULL |       NULL |
#|  7 | sysadmin             | NULL |       NULL |
#|  8 | netadmin             | NULL |       NULL |
#|  9 | developer            | NULL |       NULL |
#| 10 | DNS_Admin            | NULL |       NULL |
#+----+----------------------+------+------------+
#
# user = no any role

ROLES = (
    ('Admin', 'Global Admin'),
    ('user', 'User'),
)


class InviteForm(Form):
    email = EmailField('Email', [Required()])
    role = SelectField(u'Role', choices=ROLES)
    

class InviteRegisterForm(Form):
    email = HiddenField()
    username = HiddenField()
    password = PasswordField('Password', [Required()])