import functools
import ldap
import MySQLdb
import urllib

from datetime import datetime

from flask import g, flash, render_template, request, redirect, url_for, session
from flaskext.wtf import Form, HiddenField, TextField, PasswordField, Required

from storm.exceptions import NotOneError

from C4GD_web import app
from models import *

def get_next_url():
    """
    Defines URI to redirect to after login.
    It is provided as element "next" of request.args(GET) or request.form(POST).
    If it is not we use endpoint name from  app config DEFAULT_NEXT_TO_LOGIN_VIEW.
    
    Context: view.
    """
    if request.method == 'POST':
        d = request.form
    else:
        d = request.args
    return d.get('next', url_for(app.config['DEFAULT_NEXT_TO_LOGIN_VIEW']))

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


def mapped_dict(d, mapping):
    """
    Returns dictionary with keys coming from `mapping` and values taken
    from `d` for already translated keys (`mapping` values are keys in `d`).
    
    :param d: the dictionary providing values for result
    :param mapping: the dictionary defining mapping of keys
    
    Context: everywhere
    """
    return dict([(k, d[v]) for k, v in mapping.items()])

def obtain_token(username):
    """
    Returns last valid keystone token for the username.
    Returns None if nothing found.
    
    :param username: valid username
    
    Context: view
    """

    import pdb; pdb.set_trace()

# ldap validator
def are_ldap_authenticated(username, password):
    """
    Validates username and password with LDAP.
    
    Context: view
    """
    connection = ldap.initialize(app.config['LDAP_URI'])
    dn = 'uid=%s,%s' % (
        ldap.dn.escape_dn_chars(username),
        app.config['LDAP_BASEDN'])
    try:
        connection.simple_bind_s(dn, password)
    except ldap.INVALID_CREDENTIALS:
        return False
    else:
        return True
    finally:
        connection.unbind()

@app.before_request
def load_authenticated_user():
    if 'user_id' in session:
        g.user = g.store.find(
            User, id=session['user_id'], enabled=True).one()

def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if hasattr(g, 'user'):
            return view(*args, **kwargs)
        else:
            return redirect(
                '%s?%s' % (
                    url_for('login'),
                    urllib.urlencode(
                        {app.config['NEXT_TO_LOGIN_ARG']: request.path})))
    return wrapped

@app.context_processor
def auth_processor():
    return {'user': getattr(g, 'user', None)}

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = get_login_form()()
    if form.validate_on_submit():
        if are_ldap_authenticated(form.username.data, form.password.data):
            try:
                g.user = g.store.find(
                    User,
                    name=form.username.data, enabled=True).one()
            except NotOneError:
                flash('No enabled user `%s` in Keystone database' % \
                          form.username.data, 'error')
            else:
                session['user_id'] = g.user.id
                flash('You were logged in', 'success')
                return redirect(form.next.data)
        else:
            flash('Wrong username/password', 'error')
    return render_template('login.html', form=form)

@app.route('/')
@login_required
def index():
    return render_template(
        'index.html',
        user_roles=g.store.find(UserRole, user_id=g.user.id))

@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    flash('You were logged out', 'success')
    return redirect(url_for(app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))
